"""Parity gate: every data attribute edgar's Prospectus424B exposes is on the wire.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.prospectus_424b import Prospectus424BData

_BONE = "0001641172-25-017063"  # 424B4 priced IPO (Bone Biologics) -- cover/pricing/dilution/cap present


@pytest.fixture(scope="module")
def prospectus():
    filing = get_by_accession_number_enriched(_BONE)
    assert filing is not None, f"fixture for {_BONE} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for a 424B"
    return obj


def test_prospectus_424b_full_fidelity(prospectus) -> None:
    edgar_data = data_surface(prospectus)
    wire_fields = set(Prospectus424BData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"
