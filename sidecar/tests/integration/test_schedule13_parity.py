"""Parity gate: every data attribute edgar's Schedule13D/Schedule13G expose is on the wire.

Two objects, two gates. The cover-page nested dataclasses (ReportingPerson, IssuerInfo,
SecurityInfo, Signature) and the per-form items dataclasses are checked field-by-field via
dataclasses.fields, so a new edgar field fails loudly. Uses data_surface() for auto-filtered
attribute discovery.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched
from edgar.beneficial_ownership.models import (
    IssuerInfo,
    ReportingPerson,
    Schedule13DItems,
    Schedule13GItems,
    SecurityInfo,
    Signature,
)

from app.models.forms.schedule13 import Schedule13DData, Schedule13GData

_COMPOSECURE_13D = "0001493152-26-002882"  # rich structured 13D: 9 group filers, Item 4, CIKs present
_FMR_13G = "0000315066-26-001210"  # rich structured 13G/A: institutional (FMR/Fidelity), rule 13d-1(b)

# Edgar names that map to different wire field names (both 13D and 13G share these renames)
_RENAMES = {
    "issuer_info": "issuer",
    "security_info": "security",
}


@pytest.fixture(scope="module")
def schedule_13d():
    filing = get_by_accession_number_enriched(_COMPOSECURE_13D)
    assert filing is not None, f"fixture for {_COMPOSECURE_13D} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "Schedule13D"
    return obj


@pytest.fixture(scope="module")
def schedule_13g():
    filing = get_by_accession_number_enriched(_FMR_13G)
    assert filing is not None, f"fixture for {_FMR_13G} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "Schedule13G"
    return obj


def test_schedule13d_full_fidelity(schedule_13d) -> None:
    edgar_data = data_surface(schedule_13d)
    wire_fields = set(Schedule13DData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"


def test_schedule13g_full_fidelity(schedule_13g) -> None:
    edgar_data = data_surface(schedule_13g)
    wire_fields = set(Schedule13GData.model_fields.keys()) - {"kind"}

    edgar_on_wire = {_RENAMES.get(a, a) for a in edgar_data}

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"


def test_reporting_person_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(ReportingPerson)} == {
        "cik",
        "name",
        "citizenship",
        "sole_voting_power",
        "shared_voting_power",
        "sole_dispositive_power",
        "shared_dispositive_power",
        "aggregate_amount",
        "percent_of_class",
        "type_of_reporting_person",
        "fund_type",
        "comment",
        "member_of_group",
        "is_aggregate_exclude_shares",
        "no_cik",
    }
    # total_voting_power / total_dispositive_power are derived sums (sole + shared), not stored
    # fields; consumers add the two captured halves, so they are not mirrored as wire fields
    assert isinstance(ReportingPerson.total_voting_power, property)
    assert isinstance(ReportingPerson.total_dispositive_power, property)


def test_issuer_info_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(IssuerInfo)} == {"cik", "name", "cusip", "address"}


def test_security_info_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(SecurityInfo)} == {"title", "cusip"}


def test_signature_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(Signature)} == {"reporting_person", "signature", "title", "date"}


def test_schedule13d_items_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(Schedule13DItems)} == {
        "item1_security_title",
        "item1_issuer_name",
        "item1_issuer_address",
        "item2_filing_persons",
        "item2_business_address",
        "item2_principal_occupation",
        "item2_convictions",
        "item2_citizenship",
        "item3_source_of_funds",
        "item4_purpose_of_transaction",
        "item5_percentage_of_class",
        "item5_number_of_shares",
        "item5_transactions",
        "item5_shareholders",
        "item5_date_5pct_ownership",
        "item6_contracts",
        "item7_exhibits",
    }


def test_schedule13g_items_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(Schedule13GItems)} == {
        "item1_issuer_name",
        "item1_issuer_address",
        "item2_filer_names",
        "item2_filer_addresses",
        "item2_citizenship",
        "item3_not_applicable",
        "item4_amount_beneficially_owned",
        "item4_percent_of_class",
        "item4_sole_voting",
        "item4_shared_voting",
        "item4_sole_dispositive",
        "item4_shared_dispositive",
        "item5_not_applicable",
        "item5_ownership_5pct_or_less",
        "item6_not_applicable",
        "item7_not_applicable",
        "item8_not_applicable",
        "item9_not_applicable",
        "item10_certification",
    }
