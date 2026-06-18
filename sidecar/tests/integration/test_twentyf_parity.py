"""Parity gate: every data attribute edgar's TwentyF exposes is on the wire.

Auto-filters methods, DataFrame views, and heavy edgar domain objects.
Compares against the actual Pydantic wire model. Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.twentyf import TwentyFData

_CHECKPOINT_20F = "0001178913-26-001932"

_RENAMES = {"period_of_report": "report_period"}


@pytest.fixture(scope="module")
def twenty_f():
    filing = get_by_accession_number_enriched(_CHECKPOINT_20F)
    assert filing is not None, f"fixture for {_CHECKPOINT_20F} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "TwentyF"
    return obj


def test_twentyf_full_fidelity(twenty_f) -> None:
    edgar_data = data_surface(twenty_f)
    wire_fields = set(TwentyFData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"
