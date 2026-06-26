"""Parity gate: every data attribute edgar's Effect exposes is on the wire.

effectiveness_data (plain class backing store) is excluded -- every useful field is
exposed as a direct property except file_number, which is mapped as source_file_number.

Auto-filters methods. Compares against the actual Pydantic wire model.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.effect import EffectData

_AIM = "9999999995-26-002094"

_EXCLUDE = {"effectiveness_data"}

_EXTRA_WIRE = {"form", "source_file_number"}


@pytest.fixture(scope="module")
def effect_obj():
    filing = get_by_accession_number_enriched(_AIM)
    assert filing is not None, f"fixture for {_AIM} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an EFFECT"
    return obj


def test_effect_full_fidelity(effect_obj) -> None:
    edgar_data = data_surface(effect_obj) - _EXCLUDE
    wire_fields = set(EffectData.model_fields.keys()) - {"kind"} - _EXTRA_WIRE

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them: {sorted(not_on_wire)}"
