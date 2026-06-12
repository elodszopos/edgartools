"""Unit: the sidecar EFTS param builder stays in lockstep with edgartools' public builder.

The sidecar delegates wire encoding to edgar.search.build_efts_params and only layers its
own pagination offset on top. These pure-function assertions prove that delegation, so the
two encoders cannot silently drift (the prior code duplicated the encoding by hand).
"""

from __future__ import annotations

from datetime import date

from edgar.search.efts import build_efts_params

from app.routers.search import _build_efts_params


def test_build_efts_params_matches_public_builder_with_pagination() -> None:
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
    # sidecar output == public wire params plus the pagination offset, nothing else
    assert sidecar == {**public, "from": 40}


def test_build_efts_params_omits_from_at_offset_zero() -> None:
    sidecar = _build_efts_params("apple", None, None, None, None, None, 0)
    public = build_efts_params("apple")
    assert sidecar == public
    assert "from" not in sidecar
