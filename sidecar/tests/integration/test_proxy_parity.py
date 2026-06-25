"""Parity gate: every data attribute edgar's ProxyStatement exposes is on the wire.

DEF 14A and every 14A variant share the one ProxyStatement object, so this gate covers
the whole proxy family. Uses data_surface() for auto-filtered attribute discovery.
"""

from __future__ import annotations

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched

from app.models.forms.proxy import ProxyData

_AMD = "0001193125-26-129057"  # rich DEF 14A: full PVP XBRL + every HTML comp table


@pytest.fixture(scope="module")
def proxy():
    filing = get_by_accession_number_enriched(_AMD)
    assert filing is not None, f"fixture for {_AMD} missing"
    obj = filing.obj()
    assert obj is not None, "filing.obj() returned None for a DEF 14A"
    return obj


_TABLE_WIRE_FIELDS = {
    "executive_compensation",
    "pay_vs_performance",
    "awards_close_to_mnpi",
    "summary_compensation_table",
    "director_compensation_table",
    "beneficial_ownership",
}


def test_proxy_full_fidelity(proxy) -> None:
    edgar_data = data_surface(proxy)
    wire_fields = set(ProxyData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {a for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"


def test_proxy_table_wire_fields_present() -> None:
    """DataFrame properties are filtered by data_surface; this guard catches schema drift."""
    wire_fields = set(ProxyData.model_fields.keys())
    missing = _TABLE_WIRE_FIELDS - wire_fields
    assert not missing, f"table fields missing from ProxyData: {sorted(missing)}"
