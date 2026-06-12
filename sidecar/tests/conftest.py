"""Shared pytest harness: VCR wiring (fork conventions), SEC recording budget guard,
identity defaults for replay, and the golden-dump helper (plan: edgar-sidecar.md)."""

from __future__ import annotations

import inspect
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

CASSETTES_DIR = Path(__file__).parent / "cassettes"
GOLDENS_DIR = Path(__file__).parent.parent / "ts" / "fixtures" / "responses"

# plan "SEC recording budget": hard cap on NEW interactions recorded per pytest run
SEC_RECORDING_BUDGET = 60
_new_recordings = {"count": 0}


def _budget_guard(response: dict) -> dict:
    # vcrpy runs before_record_response on BOTH record-appends and cassette loads
    # (Cassette._load replays every stored interaction through append) - count only
    # true recordings, or shared multi-test cassettes blow the budget on replay alone
    frame = inspect.currentframe()
    while frame is not None:
        code = frame.f_code
        if code.co_name == "_load" and code.co_filename.endswith("cassette.py"):
            return response
        frame = frame.f_back
    _new_recordings["count"] += 1
    if _new_recordings["count"] > SEC_RECORDING_BUDGET:
        raise RuntimeError(
            f"SEC recording budget exceeded: more than {SEC_RECORDING_BUDGET} new HTTP "
            "interactions recorded in one run (plan: edgar-sidecar.md, recording budget)"
        )
    return response


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    # pin one shared cassette dir; pytest-vcr's default is per-test-file
    return str(CASSETTES_DIR)


@pytest.fixture(scope="module")
def vcr_config():
    # mirrors fork tests/conftest.py vcr_config
    return {
        "cassette_library_dir": str(CASSETTES_DIR),
        "record_mode": "once",
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "filter_headers": ["User-Agent", "Authorization"],
        "decode_compressed_response": True,
        "before_record_response": _budget_guard,
    }


@pytest.fixture(scope="session", autouse=True)
def _isolated_edgar_data_dir(tmp_path_factory: pytest.TempPathFactory) -> None:
    # edgartools keeps a 30-min disk HTTP cache (~/.edgar/_tcache); a warm cache would
    # swallow requests before VCR sees them -> cassettes silently missing interactions.
    # A fresh tmp dir per session keeps record AND replay deterministic.
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(tmp_path_factory.mktemp("edgar-data"))


@pytest.fixture(scope="session", autouse=True)
def _default_identity() -> None:
    # cassette replay needs no real identity; recording uses the caller's exported env.
    # session scope: must be set before module-scoped TestClient fixtures boot the app.
    os.environ.setdefault("EDGAR_IDENTITY", "edgar-sidecar tests test@example.com")
    os.environ.setdefault("SEC_EDGAR_USER_AGENT", "edgar-sidecar tests test@example.com")


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
