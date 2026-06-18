"""Parity gate: every data attribute edgar's TenK exposes is on the wire.

Auto-filters methods, DataFrame views, and heavy edgar domain objects.
Compares against the actual Pydantic wire model. Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched
from edgar.company_reports.subsidiaries import Subsidiary

from app.models.forms.tenk import TenKData

_NVDA_10K = "0001045810-25-000023"

_RENAMES = {
    "period_of_report": "report_period",
}


@pytest.fixture(scope="module")
def ten_k():
    filing = get_by_accession_number_enriched(_NVDA_10K)
    assert filing is not None, f"fixture for {_NVDA_10K} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "TenK"
    return obj


def test_tenk_full_fidelity(ten_k) -> None:
    edgar_data = data_surface(ten_k)
    wire_fields = set(TenKData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_subsidiary_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(Subsidiary)} == {"name", "jurisdiction", "ownership_pct"}
