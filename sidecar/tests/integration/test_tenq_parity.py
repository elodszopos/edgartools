"""Parity gate: every data attribute edgar's TenQ exposes is on the wire.

Auto-filters methods, DataFrame views, and heavy edgar domain objects.
Compares against the actual Pydantic wire model. Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.tenq import TenQData

_AAPL_10Q = "0000320193-26-000006"

_RENAMES = {"period_of_report": "report_period"}


@pytest.fixture(scope="module")
def ten_q():
    filing = get_by_accession_number_enriched(_AAPL_10Q)
    assert filing is not None, f"fixture for {_AAPL_10Q} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "TenQ"
    return obj


def test_tenq_full_fidelity(ten_q) -> None:
    edgar_data = data_surface(ten_q)
    wire_fields = set(TenQData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"
