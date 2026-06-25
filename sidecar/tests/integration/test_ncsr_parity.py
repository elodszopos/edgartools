"""Parity gate: every data attribute edgar's FundShareholderReport exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.ncsr import NcsrData

_BNY_MUNI = "0000797923-25-000001"


@pytest.fixture(scope="module")
def shareholder_report():
    filing = get_by_accession_number_enriched(_BNY_MUNI)
    assert filing is not None, f"fixture for {_BNY_MUNI} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an N-CSR"
    return obj


_STRUCTURAL = {
    "funds",
    "share_classes",
}


def test_ncsr_full_fidelity(shareholder_report) -> None:
    edgar_data = data_surface(shareholder_report)
    wire_fields = set(NcsrData.model_fields.keys()) - {"kind"}

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_ncsr_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(NcsrData.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from NcsrData: {sorted(missing)}"
