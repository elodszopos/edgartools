"""Parity gate: every data attribute edgar's Form144 exposes is on the wire.

Uses data_surface() for auto-filtered attribute discovery. The wire model carries
the as-filed tables and notice signature; edgar's analytical layer (totals, percentages,
holding-period math, 10b5-1 inference, anomaly flags) is client-derivable from the
captured raw rows.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.form144 import Form144Data

_ABEONA_144 = "0001972481-25-000063"  # ABEONA 144: full single-security structure, 10b5-1 plan


@pytest.fixture(scope="module")
def form_144():
    filing = get_by_accession_number_enriched(_ABEONA_144)
    assert filing is not None, f"fixture for {_ABEONA_144} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "Form144"
    return obj


def test_form144_full_fidelity(form_144) -> None:
    edgar_data = data_surface(form_144)
    wire_fields = set(Form144Data.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"
