"""Parity gate: the Fact wire model captures every data attribute of FinancialFact.

Uses data_surface() to auto-filter methods/helpers, then compares what remains
against the wire model. Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

from conftest import data_surface
from edgar.entity.models import FinancialFact

from app.models.facts import Fact

_DUMMY_FACT = FinancialFact(
    concept="us-gaap:Revenue",
    taxonomy="us-gaap",
    label="Revenue",
    value=1000.0,
    numeric_value=1000.0,
    unit="USD",
)


def test_fact_model_captures_every_financialfact_field() -> None:
    edgar_data = data_surface(_DUMMY_FACT)
    wire_fields = set(Fact.model_fields.keys())

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"FinancialFact exposes these but Fact wire model doesn't have them — map them: {sorted(not_on_wire)}"
