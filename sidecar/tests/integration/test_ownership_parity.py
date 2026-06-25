"""Parity gate: every data attribute edgar's Ownership exposes is on the wire.

Auto-filters methods. Auto-detects DataFrame views. Compares against the actual
Pydantic wire model — zero hand-maintained exclusion lists.
"""

from __future__ import annotations

import dataclasses

import pandas as pd
import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched
from edgar.ownership.owners import Owner
from edgar.ownership.tables import (
    DerivativeHolding,
    DerivativeTransaction,
    NonDerivativeHolding,
    NonDerivativeTransaction,
)

from app.models.forms.ownership import OwnershipData

_IONIS = "0000874015-26-000183"

# Table-based wire fields: one edgar compound container becomes multiple typed lists on the wire.
# data_surface filters these containers (non-dataclass edgar objects), so the introspection gate
# cannot discover them automatically. This explicit set guarantees they exist on the wire model.
_TABLE_WIRE_FIELDS = {
    "non_derivative_holdings",
    "non_derivative_transactions",
    "derivative_holdings",
    "derivative_transactions",
}


def _tabular_views(obj, attrs: set[str]) -> set[str]:
    """Attributes returning DataFrames or DataHolder — views of data already on the wire as typed records."""
    views = set()
    for name in attrs:
        try:
            val = getattr(obj, name)
            if isinstance(val, pd.DataFrame) or type(val).__name__ == "DataHolder":
                views.add(name)
        except Exception:
            pass
    return views


@pytest.fixture(scope="module")
def ownership():
    filing = get_by_accession_number_enriched(_IONIS)
    assert filing is not None, f"fixture for {_IONIS} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for a Form 4"
    return obj


def test_ownership_full_fidelity(ownership) -> None:
    edgar_data = data_surface(ownership)
    tabular = _tabular_views(ownership, edgar_data)
    wire_fields = set(OwnershipData.model_fields.keys()) - {"kind"}

    edgar_on_wire: set[str] = set()
    for attr in edgar_data - tabular:
        edgar_on_wire.add(attr)

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them — map them: {sorted(not_on_wire)}"


def test_table_wire_fields_present() -> None:
    """Explicit guard: table-based fields exist on the wire model (data_surface can't discover them)."""
    wire_fields = set(OwnershipData.model_fields.keys())
    missing = _TABLE_WIRE_FIELDS - wire_fields
    assert not missing, f"table wire fields missing from OwnershipData: {sorted(missing)}"


def test_non_derivative_holding_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(NonDerivativeHolding)} == {
        "security",
        "shares",
        "direct",
        "nature_of_ownership",
    }


def test_derivative_holding_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(DerivativeHolding)} == {
        "security",
        "underlying",
        "exercise_price",
        "exercise_date",
        "expiration_date",
        "underlying_shares",
        "direct_indirect",
        "nature_of_ownership",
    }


def test_non_derivative_transaction_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(NonDerivativeTransaction)} == {
        "security",
        "date",
        "shares",
        "remaining",
        "price",
        "acquired_disposed",
        "direct_indirect",
        "form",
        "transaction_code",
        "transaction_type",
        "equity_swap",
        "footnotes",
    }


def test_derivative_transaction_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(DerivativeTransaction)} == {
        "security",
        "underlying",
        "underlying_shares",
        "exercise_price",
        "exercise_date",
        "expiration_date",
        "shares",
        "direct_indirect",
        "price",
        "acquired_disposed",
        "date",
        "remaining",
        "form",
        "transaction_code",
        "equity_swap",
        "footnotes",
    }


def test_owner_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(Owner)} == {
        "cik",
        "is_company",
        "name",
        "name_unreversed",
        "address",
        "is_director",
        "is_officer",
        "is_other",
        "is_ten_pct_owner",
        "officer_title",
    }
    assert isinstance(Owner.position, property)
