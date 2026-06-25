"""Parity gate: every data attribute edgar's MoneyMarketFund exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.nmfp import NmfpData

_PRIME = "0001145549-25-016960"  # N-MFP3, Invesco Premier Portfolio (Prime, repos, multi-class)


@pytest.fixture(scope="module")
def money_market_fund():
    filing = get_by_accession_number_enriched(_PRIME)
    assert filing is not None, f"fixture for {_PRIME} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an N-MFP3"
    return obj


_STRUCTURAL = {
    "general_info",
    "series_info",
    "share_classes",
    "securities",
}


def test_nmfp_full_fidelity(money_market_fund) -> None:
    edgar_data = data_surface(money_market_fund)
    wire_fields = set(NmfpData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_nmfp_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(NmfpData.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from NmfpData: {sorted(missing)}"
