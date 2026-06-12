"""Shared pytest harness: URL-keyed SEC fixture store + httpx replay transport,
isolated edgartools data dir, identity defaults, and the golden-dump helper
(plan: edgar-sidecar.md; store: tests/sec_replay.py)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import sec_replay

GOLDENS_DIR = Path(__file__).parent.parent / "ts" / "fixtures" / "responses"


@pytest.fixture(scope="session", autouse=True)
def _isolated_edgar_data_dir(tmp_path_factory: pytest.TempPathFactory) -> None:
    # Pin a clean per-session data dir so no stray local cache/state leaks into tests.
    # The replay transport is the sole arbiter of SEC bytes (cache disabled), but edgartools
    # also keeps other local data under this dir -- a fresh dir keeps every run deterministic.
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(tmp_path_factory.mktemp("edgar-data"))


@pytest.fixture(scope="session", autouse=True)
def _default_identity() -> None:
    # replay needs no real identity; recording uses the caller's exported env.
    # session scope: must be set before module-scoped TestClient fixtures boot the app.
    os.environ.setdefault("EDGAR_IDENTITY", "edgar-sidecar tests test@example.com")
    os.environ.setdefault("SEC_EDGAR_USER_AGENT", "edgar-sidecar tests test@example.com")


@pytest.fixture(scope="session", autouse=True)
def _sec_transport(_isolated_edgar_data_dir: None, _default_identity: None):
    # Single chokepoint: patch httpx.HTTPTransport / AsyncHTTPTransport so EVERY SEC request
    # (edgartools' HTTP_MGR clients AND its direct httpx.get/httpx.Client call sites) resolves
    # to the fixture store. Default = replay (miss is a hard error, never a silent network call);
    # EDGAR_FIXTURE_RECORD=1 = record. Session-scoped so the patch spans the whole run.
    mp = pytest.MonkeyPatch()
    if os.environ.get("EDGAR_FIXTURE_RECORD") == "1":
        sec_replay.install_record(mp)
    else:
        sec_replay.install_replay(mp)
    yield
    mp.undo()
    from edgar.httpclient import HTTP_MGR

    HTTP_MGR.close()  # drop the replay-bound client so later imports rebuild normally


@pytest.fixture
def golden() -> Callable[[str, str, Any], None]:
    """Assert payload matches the committed golden byte-for-byte.

    Missing file or GOLDEN_UPDATE=1 writes it (commit the diff with an explanation -
    plan: golden lifecycle). Goldens feed the generated-Zod validation suite (U03).
    """

    def _check(endpoint: str, case: str, payload: Any) -> None:
        path = GOLDENS_DIR / endpoint / f"{case}.json"
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if os.environ.get("GOLDEN_UPDATE") == "1" or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            return
        committed = path.read_text(encoding="utf-8")
        assert committed == rendered, (
            f"golden mismatch for {endpoint}/{case}; if the change is intentional, rerun "
            "with GOLDEN_UPDATE=1 and explain the diff in the commit message"
        )

    return _check
