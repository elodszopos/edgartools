"""The committed OpenAPI snapshot must document the exact query parameters (names + required
flags) of the key list endpoints. Pins the request contract so a param can't be renamed, dropped,
or flipped required/optional unnoticed. Reads the snapshot -- never regenerates it."""

from __future__ import annotations

import json
from pathlib import Path

_OPENAPI = Path(__file__).resolve().parent.parent.parent / "openapi.json"


def _query_params(path: str) -> dict[str, bool]:
    spec = json.loads(_OPENAPI.read_text(encoding="utf-8"))
    params = spec["paths"][path]["get"].get("parameters", [])
    return {p["name"]: bool(p.get("required", False)) for p in params if p["in"] == "query"}


def test_filings_list_query_params() -> None:
    assert _query_params("/filings") == {
        "year": False,
        "quarter": False,
        "form": False,
        "amendments": False,
        "date_from": False,
        "date_to": False,
        "id": False,
        "start": False,
        "page_size": False,
    }


def test_search_query_params() -> None:
    assert _query_params("/search") == {
        "q": False,
        "forms": False,
        "items": False,
        "id": False,
        "date_from": False,
        "date_to": False,
        "start": False,
        "page_size": False,
    }


def test_financials_query_params() -> None:
    assert _query_params("/company/{id}/financials") == {
        "period": False,
        "view": False,
        "dimensions": False,
        "amendments": False,
    }
