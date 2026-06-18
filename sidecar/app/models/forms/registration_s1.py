"""Typed `data` for the S-1 / F-1 registration statement (edgar `RegistrationS1`).

`filing.obj()` returns one `RegistrationS1` for both S-1 and F-1 (and their /A amendments) -- the
domestic and foreign IPO/resale registration forms share the object, so they share this model; the
specific form is the `form` field. Captured legs: the cover page (S1CoverPage: filer category, rule
checkboxes, SIC/EIN), the offering-type classification, the Exhibit 107 fee table, the four
own-document table extractions (selling stockholders, dilution, capitalization, underwriting), and
the top-level convenience scalars (registration_number, ein, sic_code, state_of_incorporation,
total_offering, net_fee, securities). The table extractors reuse the shared `offering.py` wire
models. Cross-entity lifecycle navigation (takedowns, related_filings, effective_date, is_effective)
is present as nullable fields set to None in the converter -- they require additional SEC fetches.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel
from app.models.forms.offering import (
    OfferingCapitalization,
    OfferingDilution,
    OfferingFeeSecurity,
    OfferingFeeTable,
    OfferingSellingStockholders,
    OfferingUnderwriting,
)


class S1CoverPage(WireModel):
    """S-1 cover-page fields (filer-category + rule checkboxes, SIC/EIN, security description)."""

    company_name: str
    registration_number: str | None
    state_of_incorporation: str | None
    sic_code: str | None
    ein: str | None

    # filer-category checkboxes (null when the box state cannot be read from the cover)
    is_large_accelerated_filer: bool | None
    is_accelerated_filer: bool | None
    is_non_accelerated_filer: bool | None
    is_smaller_reporting_company: bool | None
    is_emerging_growth_company: bool | None

    # rule checkboxes (edgar defaults each to False when unchecked/absent)
    is_rule_415: bool  # delayed/continuous offering (shelf)
    is_rule_462b: bool  # immediate-effectiveness additional-securities registration
    is_rule_462e: bool  # automatic shelf (WKSI)

    security_description: str | None
    confidence: str  # extraction confidence: "low" / "medium" / "high"


# edgar S1OfferingType enum values (the .value strings)
S1OfferingTypeLiteral = Literal["ipo", "spac", "resale", "debt", "follow_on", "unknown"]


class RegistrationS1Data(WireModel):
    """filing.obj() for an S-1/F-1 (and /A) -- the edgar RegistrationS1 object, full fidelity."""

    kind: Literal["registration_s1"] = "registration_s1"
    form: str  # the specific variant: "S-1", "S-1/A", "F-1", "F-1/A"
    company: str | None
    filing_date: str | None
    accession_number: str | None
    is_amendment: bool
    offering_type: S1OfferingTypeLiteral  # IPO / SPAC / resale / debt / follow-on classification

    # convenience scalars (delegate to cover_page; on the wire for flat access)
    registration_number: str | None
    ein: str | None
    sic_code: str | None
    state_of_incorporation: str | None

    # fee-table convenience scalars + per-security breakdown
    total_offering: float | None  # from fee_table.total_offering_amount
    net_fee: float | None  # from fee_table.net_fee_due
    securities: list[OfferingFeeSecurity]  # from fee_table.securities (empty when no exhibit)

    cover_page: S1CoverPage  # always present (from_filing always builds it)
    fee_table: OfferingFeeTable | None  # Exhibit 107 fee table; null when the exhibit is absent

    # own-document table extractions (null when the section is not present in the filing)
    selling_stockholders: OfferingSellingStockholders | None  # chiefly resale registrations
    dilution: OfferingDilution | None  # chiefly IPO registrations
    capitalization: OfferingCapitalization | None  # chiefly IPO registrations
    underwriting: OfferingUnderwriting | None

    # cross-entity fetch, served separately
    is_effective: bool | None = None
    effective_date: str | None = None
    related_filings: None = None
    takedowns: None = None
