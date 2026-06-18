"""Unit: EFTS param-building wire shape, and that the router wrapper only adds pagination.

edgar.search.efts keeps param-building private, so /search builds EFTS query params
in app.efts.build_efts_params. These assertions pin the exact wire shape and prove
_build_efts_params layers only its pagination offset on top.
"""

from __future__ import annotations

from datetime import date

from app.efts import build_efts_params
from app.routers.search import _build_efts_params


def test_build_efts_params_wire_shape() -> None:
    params = build_efts_params(
        "supply chain",
        forms=["10-K", "10-Q"],
        items=["1.05"],
        cik="0000320193",
        start_date="2024-01-01",
        end_date="2024-03-31",
    )
    assert params == {
        "q": "supply chain",
        "forms": "10-K,10-Q",
        "items": "1.05",
        "dateRange": "custom",
        "startdt": "2024-01-01",
        "enddt": "2024-03-31",
        "ciks": "0000320193",
    }


def test_router_wrapper_adds_only_pagination() -> None:
    sidecar = _build_efts_params(
        "supply chain",
        ["10-K", "10-Q"],
        ["1.05"],
        "0000320193",
        date(2024, 1, 1),
        date(2024, 3, 31),
        40,
    )
    public = build_efts_params(
        "supply chain",
        forms=["10-K", "10-Q"],
        items=["1.05"],
        cik="0000320193",
        start_date="2024-01-01",
        end_date="2024-03-31",
    )
    # wrapper output == builder params plus the pagination offset, nothing else
    assert sidecar == {**public, "from": 40}


def test_build_efts_params_omits_from_at_offset_zero() -> None:
    sidecar = _build_efts_params("apple", None, None, None, None, None, 0)
    assert sidecar == build_efts_params("apple") == {"q": "apple"}
    assert "from" not in sidecar
