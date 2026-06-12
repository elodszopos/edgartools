"""Shared pytest harness: URL-keyed SEC fixture store + httpx replay transport,
isolated edgartools data dir, identity defaults, the golden-dump helper, and the
live-marker deselection wiring (plan: edgar-sidecar.md; store: tests/sec_replay.py)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import sec_replay

GOLDENS_DIR = Path(__file__).parent.parent / "ts" / "fixtures" / "responses"

# /health embeds the edgartools package version, which changes every release; normalized to a
# stable sentinel so the golden stays version-independent.
_VERSION_SENTINEL = "<edgartools-version>"


def _live_selected(config: pytest.Config) -> bool:
    # Live tests hit the real SEC; treated as selected ONLY on explicit opt-in via `-m live`
    # or RUN_LIVE=1. `-m "not live"` must NOT count as opting in.
    if os.environ.get("RUN_LIVE") == "1":
        return True
    markexpr = config.getoption("markexpr", default="") or ""
    if re.search(r"\bnot\s+live\b", markexpr):
        return False
    return bool(re.search(r"\blive\b", markexpr))


def pytest_configure(config: pytest.Config) -> None:
    # Self-sufficient marker registration for deselection; a duplicate of the pyproject entry is harmless.
    config.addinivalue_line("markers", "live: true SEC round-trip, opt-in (excluded from default gates)")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    # Default-deselect live tests (conftest-side equivalent of addopts `-m "not live"`): skip every
    # live-marked item unless live was explicitly selected.
    if _live_selected(config):
        return
    skip_live = pytest.mark.skip(reason="live test: opt in with -m live or RUN_LIVE=1")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session", autouse=True)
def _isolated_edgar_data_dir(tmp_path_factory: pytest.TempPathFactory) -> None:
    # Pin a clean per-session data dir so no stray local cache/state leaks into tests.
    # The replay transport is the sole arbiter of SEC bytes (cache disabled), but edgartools
    # also keeps other local data under this dir -- a fresh dir keeps every run deterministic.
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(tmp_path_factory.mktemp("edgar-data"))


@pytest.fixture(scope="session", autouse=True)
def _default_identity() -> None:
    # replay needs no real identity; recording AND the live suite use the caller's exported env.
    # session scope: must be set before module-scoped TestClient fixtures boot the app.
    os.environ.setdefault("EDGAR_IDENTITY", "edgar-sidecar tests test@example.com")
    os.environ.setdefault("SEC_EDGAR_USER_AGENT", "edgar-sidecar tests test@example.com")


@pytest.fixture(scope="session", autouse=True)
def _sec_transport(request: pytest.FixtureRequest, _isolated_edgar_data_dir: None, _default_identity: None):
    # Single chokepoint: patch httpx.HTTPTransport / AsyncHTTPTransport so EVERY SEC request
    # (edgartools' HTTP_MGR clients AND its direct httpx.get/httpx.Client call sites) resolves
    # to the fixture store. Default = replay (miss is a hard error, never a silent network call);
    # EDGAR_FIXTURE_RECORD=1 = record. Session-scoped so the patch spans the whole run.
    if _live_selected(request.config):
        # Live suite reaches the real SEC: leave httpx transports untouched (no replay, no record).
        yield
        return
    mp = pytest.MonkeyPatch()
    if os.environ.get("EDGAR_FIXTURE_RECORD") == "1":
        sec_replay.install_record(mp)
    else:
        sec_replay.install_replay(mp)
    yield
    mp.undo()
    from edgar.httpclient import HTTP_MGR

    HTTP_MGR.close()  # drop the replay-bound client so later imports rebuild normally


def _is_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() in ("1", "true", "yes")


def _normalize_for_golden(endpoint: str, obj: Any) -> Any:
    # Strip the volatile edgartools version out of the health payload before compare/write so a
    # release bump never drifts the golden.
    if endpoint == "health" and isinstance(obj, dict) and "edgartools_version" in obj:
        return {**obj, "edgartools_version": _VERSION_SENTINEL}
    return obj


def _render_pretty(obj: Any) -> str:
    # Active on-disk golden format: human-reviewable pretty JSON with a trailing newline.
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _render_wire(payload: Any) -> str:
    # Serialization-level truth: byte-identical to Starlette's JSONResponse.render output
    # (response.text) -- compact separators, ensure_ascii=False, allow_nan=False. Verified equal
    # to response.text on /health. NOT the active on-disk format yet: the committed goldens are
    # pretty-printed (_render_pretty), differing from response.text only by indentation + trailing
    # newline. Switching the active compare/write below to this requires regenerating every golden.
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


@pytest.fixture
def golden() -> Callable[[str, str, Any], None]:
    """Assert payload matches the committed golden byte-for-byte.

    Callers pass response.json(); the committed golden is the canonical pretty form feeding the
    generated-Zod validation suite (U03). The serialization-level truth (response.text, compact)
    is captured by _render_wire but is not yet the active on-disk format - the goldens are
    pretty-printed; activating it needs a regeneration pass.

    Missing golden: written locally so first-run authoring is cheap; in CI (env CI truthy) a
    missing golden FAILS instead of silently writing an unreviewed artifact. GOLDEN_UPDATE=1 forces
    a rewrite (commit the diff with an explanation - plan: golden lifecycle).

    The health golden's package version is normalized to a stable sentinel on both the rendered
    payload and the stored file, so an edgartools release never drifts it.
    """

    def _check(endpoint: str, case: str, payload: Any) -> None:
        path = GOLDENS_DIR / endpoint / f"{case}.json"
        # The payload must serialize exactly as the wire would (allow_nan=False); this trips on a
        # NaN/inf leak that pretty-printing (allow_nan=True) would silently emit as invalid JSON.
        _render_wire(payload)
        rendered = _render_pretty(_normalize_for_golden(endpoint, payload))

        if os.environ.get("GOLDEN_UPDATE") == "1":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            return

        if not path.exists():
            if _is_ci():
                pytest.fail(
                    f"golden missing for {endpoint}/{case} and CI is set: refusing to write an "
                    f"unreviewed golden in CI. Generate it locally and commit "
                    f"ts/fixtures/responses/{endpoint}/{case}.json."
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            return

        committed = path.read_text(encoding="utf-8")
        if endpoint == "health":
            # Normalize the stored side too so the existing literal-version golden keeps passing
            # across edgartools releases.
            committed = _render_pretty(_normalize_for_golden(endpoint, json.loads(committed)))
        assert committed == rendered, (
            f"golden mismatch for {endpoint}/{case}; if the change is intentional, rerun "
            "with GOLDEN_UPDATE=1 and explain the diff in the commit message"
        )

    return _check
