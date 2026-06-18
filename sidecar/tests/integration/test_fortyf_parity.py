"""Parity gate: every data attribute edgar's FortyF exposes is on the wire.

Auto-filters methods, DataFrame views, and heavy edgar domain objects.
Compares against the actual Pydantic wire model. Zero hand-maintained exclusion lists.

40-F is the lean case: its substance is the Canadian AIF + MD&A, exposed by edgar as attachment
accessors served by /content + /sections. No item index, no subsidiaries, no EX-21.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.fortyf import FortyFData

_MAGNA_40F = "0001193125-25-066935"

_RENAMES = {"period_of_report": "report_period"}

# Raw HTML/text blobs and MD&A (second SEC request) are not inline --
# served via /content + /attachments
_HEAVY_CONTENT = {
    "aif_html", "aif_text",
    "mda_html", "mda_text", "mda_attachment",
}


@pytest.fixture(scope="module")
def forty_f():
    filing = get_by_accession_number_enriched(_MAGNA_40F)
    assert filing is not None, f"fixture for {_MAGNA_40F} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "FortyF"
    return obj


def test_fortyf_full_fidelity(forty_f) -> None:
    edgar_data = data_surface(forty_f) - _HEAVY_CONTENT
    wire_fields = set(FortyFData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"
