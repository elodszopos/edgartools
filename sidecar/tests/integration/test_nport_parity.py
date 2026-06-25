"""Parity gate: every data attribute edgar's FundReport exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.nport import NPortData

_1WS = "0001752724-25-076577"  # NPORT-P, 1WS Credit Income Fund (bonds, swaps, futures, FX metrics)


@pytest.fixture(scope="module")
def fund_report():
    filing = get_by_accession_number_enriched(_1WS)
    assert filing is not None, f"fixture for {_1WS} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an NPORT-P"
    return obj


_STRUCTURAL = {
    "header",
    "general_info",
    "fund_info",
}


def test_nport_full_fidelity(fund_report) -> None:
    edgar_data = data_surface(fund_report)
    wire_fields = set(NPortData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_nport_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(NPortData.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from NPortData: {sorted(missing)}"
