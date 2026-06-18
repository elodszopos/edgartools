"""Parity gate: every data attribute edgar's FundCensus exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.

TODO(REVISIT): this gate checks only the TOP-LEVEL FundCensus surface. The nested Pydantic models
(FundSeriesInfo, LineOfCredit, LineOfCreditFacility, FundShareClass, RegistrantInfo, ServiceProvider,
BrokerDealer, ETFInfo, ...) are NOT field-checked, so a new field on any of them is silently dropped
by the converter with no gate failure -- exactly the class of gap that let share_classes go unmapped.
Add per-model `model_fields` checks (mirror test_tenk_parity's dataclasses.fields checks) as part of
the parity-gate cardinality/coverage sweep.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.ncen import NcenData

_BNY = "0001752724-25-058074"  # N-CEN, BNY Mellon Investment Funds V (governance + providers + LoC)


@pytest.fixture(scope="module")
def fund_census():
    filing = get_by_accession_number_enriched(_BNY)
    assert filing is not None, f"fixture for {_BNY} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an N-CEN"
    return obj


def test_ncen_full_fidelity(fund_census) -> None:
    edgar_data = data_surface(fund_census)
    wire_fields = set(NcenData.model_fields.keys()) - {"kind"}

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"
