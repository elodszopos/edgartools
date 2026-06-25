"""Parity gate: every data attribute edgar's RegistrationS3 exposes is on the wire.

The whole S-3/F-3 shelf family (S-3, S-3ASR, S-3D, S-3DPOS, F-3, F-3ASR and
their /A amendments) shares the one RegistrationS3 object, so this gate covers all of them.

Auto-filters methods. Compares against the actual Pydantic wire model.
Zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.registration_s3 import RegistrationS3Data

_CENTRAL_PACIFIC = "0001140361-25-024210"  # S-3 universal shelf (Central Pacific Financial) -- full fee table


@pytest.fixture(scope="module")
def s3():
    filing = get_by_accession_number_enriched(_CENTRAL_PACIFIC)
    assert filing is not None, f"fixture for {_CENTRAL_PACIFIC} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for an S-3"
    return obj


_STRUCTURAL = {
    "cover_page",
    "fee_table",
}


def test_registration_s3_full_fidelity(s3) -> None:
    edgar_data = data_surface(s3)
    wire_fields = set(RegistrationS3Data.model_fields.keys()) - {"kind"}

    not_on_wire = edgar_data - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_registration_s3_structural_fields_present() -> None:
    """Nested edgar BaseModels are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(RegistrationS3Data.model_fields.keys())
    missing = _STRUCTURAL - wire_fields
    assert not missing, f"structural fields missing from RegistrationS3Data: {sorted(missing)}"
