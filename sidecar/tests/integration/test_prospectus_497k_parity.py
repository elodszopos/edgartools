"""Parity gate: every data attribute edgar's Prospectus497K exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.prospectus_497k import Prospectus497KData

_VANGUARD = "0001683863-25-002784"  # 497K, Vanguard CA Long-Term Tax-Exempt (2 classes, full performance)


@pytest.fixture(scope="module")
def prospectus():
    filing = get_by_accession_number_enriched(_VANGUARD)
    assert filing is not None, f"fixture for {_VANGUARD} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for a 497K"
    return obj


_STRUCTURAL = {
    "share_classes",
    "performance_returns",
    "best_quarter",
    "worst_quarter",
}


def test_prospectus_497k_full_fidelity(prospectus) -> None:
    edgar_data = data_surface(prospectus)
    wire_fields = set(Prospectus497KData.model_fields.keys()) - {"kind"}

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_prospectus_497k_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(Prospectus497KData.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from Prospectus497KData: {sorted(missing)}"
