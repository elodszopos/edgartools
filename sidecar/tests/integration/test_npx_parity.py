"""Parity gate: every data attribute edgar's NPX exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
primary_doc is excluded -- it's the raw backing store; every NPX property delegates to it.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.npx import NpxData

_PROVIDENT = "0001076964-26-000007"

_EXCLUDE = {"primary_doc"}


@pytest.fixture(scope="module")
def npx_obj():
    filing = get_by_accession_number_enriched(_PROVIDENT)
    assert filing is not None, f"fixture for {_PROVIDENT} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an N-PX"
    return obj


def test_npx_full_fidelity(npx_obj) -> None:
    edgar_data = data_surface(npx_obj) - _EXCLUDE
    wire_fields = set(NpxData.model_fields.keys()) - {"kind"}

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them: {sorted(not_on_wire)}"
