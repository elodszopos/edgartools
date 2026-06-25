"""Parity gate: every data attribute edgar's DraftRegistrationStatement exposes is on the wire.

DRS and DRS/A share the one object, so this gate covers both.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.drs import DRSData

_VERDE = "0001640334-25-001090"  # DRS draft S-1 (Verde Resources) -- underlying RegistrationS1 built

# Edgar names that map to different wire field names
_RENAMES = {
    "company_name": "company",  # duplicate accessor; wire carries it as 'company'
}


@pytest.fixture(scope="module")
def drs():
    filing = get_by_accession_number_enriched(_VERDE)
    assert filing is not None, f"fixture for {_VERDE} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for a DRS"
    return obj


_STRUCTURAL = {
    "underlying_object",
}


def test_drs_full_fidelity(drs) -> None:
    edgar_data = data_surface(drs)
    wire_fields = set(DRSData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_drs_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(DRSData.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from DRSData: {sorted(missing)}"
