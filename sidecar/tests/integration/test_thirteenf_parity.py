"""Parity gate: every data attribute edgar's ThirteenF exposes is on the wire.

The nested dataclasses (FilingManager, OtherManager, CoverPage, SummaryPage, Signature,
PrimaryDocument13F) are checked field-by-field via dataclasses.fields, so a new edgar
field fails loudly. Uses data_surface() for auto-filtered attribute discovery.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import data_surface
from edgar._filings import get_by_accession_number_enriched
from edgar.thirteenf import (
    CoverPage,
    FilingManager,
    OtherManager,
    PrimaryDocument13F,
    Signature,
    SummaryPage,
)

from app.models.forms.thirteenf import Form13FData

_BML_13F_HR = "0001754960-26-000359"  # 13F-HR, 16 holdings incl. one put, dollars era
_FIG_13F_NT = "0001245521-26-000002"  # 13F-NT, no holdings (affiliated manager reports them)

# Structural transforms: one edgar attr maps to wire field(s) under a different name
_SPLITS = {
    "primary_form_information": {"cover_page", "summary", "signature", "additional_information"},
    "infotable": {"holdings"},  # DataFrame on 13F-HR (filtered by data_surface), None on 13F-NT
}
# Raw source content, not parsed structured data -- same category as 40-F's _HEAVY_CONTENT
_RAW_SOURCE = {"infotable_html"}


@pytest.fixture(scope="module")
def thirteenf():
    filing = get_by_accession_number_enriched(_BML_13F_HR)
    assert filing is not None, f"fixture for {_BML_13F_HR} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "ThirteenF"
    return obj


@pytest.fixture(scope="module")
def thirteenf_nt():
    filing = get_by_accession_number_enriched(_FIG_13F_NT)
    assert filing is not None, f"fixture for {_FIG_13F_NT} missing"
    obj = filing.obj()
    assert obj is not None and type(obj).__name__ == "ThirteenF"
    return obj


def test_thirteenf_full_fidelity(thirteenf) -> None:
    edgar_data = data_surface(thirteenf) - _RAW_SOURCE
    wire_fields = set(Form13FData.model_fields.keys()) - {"kind"}

    edgar_on_wire: set[str] = set()
    for a in edgar_data:
        if a in _SPLITS:
            edgar_on_wire |= _SPLITS[a]
        else:
            edgar_on_wire.add(a)

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"Edgar exposes these but wire model doesn't have them -- map them: {sorted(not_on_wire)}"


def test_filing_manager_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(FilingManager)} == {"name", "address"}


def test_other_manager_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(OtherManager)} == {"cik", "name", "file_number", "sequence_number"}


def test_cover_page_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(CoverPage)} == {
        "report_calendar_or_quarter",
        "report_type",
        "filing_manager",
        "other_managers",
    }


def test_summary_page_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(SummaryPage)} == {
        "other_included_managers_count",
        "total_value",
        "total_holdings",
        "other_managers",
    }


def test_signature_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(Signature)} == {
        "name",
        "title",
        "phone",
        "signature",
        "city",
        "state_or_country",
        "date",
    }


def test_primary_document_fields_captured() -> None:
    assert {f.name for f in dataclasses.fields(PrimaryDocument13F)} == {
        "report_period",
        "cover_page",
        "summary_page",
        "signature",
        "additional_information",
    }


def test_thirteenf_nt_parity(thirteenf_nt) -> None:
    """Secondary parity pass on a 13F-NT where infotable_html resolves to None cleanly."""
    edgar_data = data_surface(thirteenf_nt) - _RAW_SOURCE
    wire_fields = set(Form13FData.model_fields.keys()) - {"kind"}

    edgar_on_wire: set[str] = set()
    for a in edgar_data:
        if a in _SPLITS:
            edgar_on_wire |= _SPLITS[a]
        else:
            edgar_on_wire.add(a)

    not_on_wire = edgar_on_wire - wire_fields
    assert not not_on_wire, f"13F-NT exposes these but wire model doesn't: {sorted(not_on_wire)}"
