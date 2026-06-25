"""Shared pytest harness: URL-keyed SEC fixture store + httpx replay transport,
isolated edgartools data dir, identity defaults, the golden-dump helper, and the
live-marker deselection wiring (plan: edgar-sidecar.md; store: tests/sec_replay.py)."""

from __future__ import annotations

import dataclasses
import json
import os
import re
from collections.abc import Callable
from enum import Enum

import pandas as pd


def data_surface(obj: object) -> set[str]:
    """Public data attributes of an edgar object that belong on the wire.

    Filters out: dunder, methods, DataFrames, DataHolder, Document (parsed
    HTML tree -- served at /content), rich rendering objects, and non-trivial
    edgar domain objects (Company, Filing, Financials, etc.). Dataclass records
    and Enums from edgar pass through.
    """
    out: set[str] = set()
    for name in dir(obj):
        if name.startswith("_"):
            continue
        cls_attr = getattr(type(obj), name, None)
        if cls_attr is not None and callable(cls_attr) and not isinstance(cls_attr, property):
            continue
        try:
            val = getattr(obj, name)
        except Exception:
            continue
        if val is None:
            out.add(name)
            continue
        vtype = type(val)
        vname = vtype.__name__
        if isinstance(val, pd.DataFrame) or vname in ("DataHolder", "Document"):
            continue
        vmod = getattr(vtype, "__module__", "") or ""
        if vmod.startswith("rich."):
            continue
        if vmod.startswith("edgar.") and not (dataclasses.is_dataclass(val) or isinstance(val, Enum)):
            continue
        out.add(name)
    return out


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


_DAYS_SENTINEL = -999


def _normalize_for_golden(endpoint: str, obj: Any) -> Any:
    # Strip volatile runtime-computed values before compare/write so time-drift never breaks goldens.
    if endpoint == "health" and isinstance(obj, dict) and "edgartools_version" in obj:
        return {**obj, "edgartools_version": _VERSION_SENTINEL}
    if endpoint == "filing" and isinstance(obj, dict):
        data = obj.get("data")
        if isinstance(data, dict) and data.get("kind") == "formc" and "days_to_deadline" in data:
            return {**obj, "data": {**data, "days_to_deadline": _DAYS_SENTINEL, "is_expired": True}}
    return obj


def _render_wire(payload: Any) -> str:
    # The on-disk golden format IS the wire: byte-identical to Starlette's JSONResponse.render
    # output (response.text) -- compact separators, ensure_ascii=False, allow_nan=False (a
    # NaN/inf leak fails serialization here exactly as it would on the wire).
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


@pytest.fixture
def golden() -> Callable[[str, str, Any], None]:
    """Assert payload matches the committed golden byte-for-byte.

    Callers pass response.json(); the committed golden is wire-exact compact JSON
    (identical bytes to response.text) feeding the generated-Zod validation suite (U03).

    Missing golden: written locally so first-run authoring is cheap; in CI (env CI truthy) a
    missing golden FAILS instead of silently writing an unreviewed artifact. GOLDEN_UPDATE=1 forces
    a rewrite (commit the diff with an explanation - plan: golden lifecycle).

    The health payload's package version is normalized to a stable sentinel before compare/write
    (the stored golden carries the sentinel), so an edgartools release never drifts it.
    """

    def _check(endpoint: str, case: str, payload: Any) -> None:
        path = GOLDENS_DIR / endpoint / f"{case}.json"
        rendered = _render_wire(_normalize_for_golden(endpoint, payload))

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
        assert committed == rendered, (
            f"golden mismatch for {endpoint}/{case}; if the change is intentional, rerun "
            "with GOLDEN_UPDATE=1 and explain the diff in the commit message"
        )

    return _check
