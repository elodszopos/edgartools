"""Parity gate: every data attribute edgar's current-report objects expose is on the wire.

Two objects, two gates: 8-K -> CurrentReport (exported EightK), 6-K -> SixK. Uses
data_surface() for auto-filtered attribute discovery.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.eightk import EightKData
from app.models.forms.sixk import SixKData

_AAPL_8K = "0000320193-26-000011"  # rich: earnings, multi-item, EX-99.1
_51TALK_6K = "0001104659-26-073181"  # rich: cover metadata, 20-F checkbox, EX-99.1


@pytest.fixture(scope="module")
def eight_k():
    filing = get_by_accession_number_enriched(_AAPL_8K)
    assert filing is not None, f"fixture for {_AAPL_8K} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "CurrentReport"
    return obj


@pytest.fixture(scope="module")
def six_k():
    filing = get_by_accession_number_enriched(_51TALK_6K)
    assert filing is not None, f"fixture for {_51TALK_6K} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "SixK"
    return obj


def test_eightk_full_fidelity(eight_k) -> None:
    edgar_data = data_surface(eight_k)
    wire_fields = set(EightKData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"


def test_sixk_full_fidelity(six_k) -> None:
    edgar_data = data_surface(six_k)
    wire_fields = set(SixKData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"
