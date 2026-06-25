"""Parity gate: every data attribute edgar's FormC exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.formc import FormCData

_GRIGGS_C = "0001669191-25-000186"  # Griggs Mutual Holdings -- plain Form C with the full structure

# Edgar names that map to different wire field names
_RENAMES = {
    "filer_information": "filer",
    "issuer_information": "issuer",
    "offering_information": "offering",
    "annual_report_disclosure": "annual_report",
    "signature_info": "signatures",
}


@pytest.fixture(scope="module")
def form_c():
    filing = get_by_accession_number_enriched(_GRIGGS_C)
    assert filing is not None, f"fixture for {_GRIGGS_C} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "FormC"
    return obj


def test_formc_full_fidelity(form_c) -> None:
    edgar_data = data_surface(form_c)
    wire_fields = set(FormCData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_formc_structural_fields_present() -> None:
    """Reverse check: nested structural blocks exist on the wire model."""
    wire_fields = set(FormCData.model_fields.keys())
    for wire_name in _RENAMES.values():
        assert wire_name in wire_fields, f"structural field {wire_name!r} missing from FormCData"
