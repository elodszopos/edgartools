"""Parity gate: every data attribute edgar's RegistrationS1 exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.registration_s1 import RegistrationS1Data

_ACCELERANT = "0001193125-25-152889"  # S-1 IPO (Accelerant Holdings) -- clean cover + underwriting


@pytest.fixture(scope="module")
def s1():
    filing = get_by_accession_number_enriched(_ACCELERANT)
    assert filing is not None, f"fixture for {_ACCELERANT} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an S-1"
    return obj


_STRUCTURAL = {
    "cover_page",
    "fee_table",
    "selling_stockholders",
    "dilution",
    "capitalization",
    "underwriting",
}


def test_registration_s1_full_fidelity(s1) -> None:
    edgar_data = data_surface(s1)
    wire_fields = set(RegistrationS1Data.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_registration_s1_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(RegistrationS1Data.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from RegistrationS1Data: {sorted(missing)}"
