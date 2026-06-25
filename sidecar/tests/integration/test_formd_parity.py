"""Parity gate: every data attribute edgar's FormD exposes is on the wire.

data_surface only discovers top-level scalar/bool properties (edgar Pydantic BaseModel
blocks like offering_data and signature_block are filtered); the structural fields guard
ensures those nested blocks are present on the wire model.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.formd import FormDData

_CENTERSEAT_D = "0002054457-25-000001"

_RENAMES = {
    "offering_data": "offering",
    "signature_block": "signatures",
}


@pytest.fixture(scope="module")
def form_d():
    filing = get_by_accession_number_enriched(_CENTERSEAT_D)
    assert filing is not None, f"fixture for {_CENTERSEAT_D} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "FormD"
    return obj


def test_formd_full_fidelity(form_d) -> None:
    edgar_data = data_surface(form_d)
    wire_fields = set(FormDData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_formd_structural_fields_present() -> None:
    """Nested edgar blocks are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(FormDData.model_fields.keys())
    for wire_name in _RENAMES.values():
        assert wire_name in wire_fields, f"structural field {wire_name!r} missing from FormDData"
