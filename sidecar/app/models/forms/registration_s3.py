"""Typed `data` for the S-3 / F-3 shelf registration statement (edgar `RegistrationS3`).

`filing.obj()` returns one `RegistrationS3` for the whole shelf family -- S-3, S-3ASR (automatic
shelf), S-3D, S-3DPOS, F-3, F-3ASR and their /A amendments; the specific form is the `form` field.
S-3 filings are short: they incorporate financials by reference from the issuer's 10-K/10-Q, so the
captured surface is the cover page (S3CoverPage: filer category + rule checkboxes, state/EIN), the
offering-type classification, the Exhibit 107 fee table (the shared `offering.py` model, reused
from S-1), and the top-level convenience scalars (registration_number, ein, state_of_incorporation,
total_offering, net_fee, fee_deferred, securities). There are NO selling-stockholder/dilution/
capitalization/underwriting legs -- those are S-1's prospectus tables, absent from the shelf cover.
Cross-entity lifecycle navigation (takedowns, related_filings) is present as nullable fields set to
None in the converter -- they require additional SEC fetches.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel
from app.models.forms.offering import OfferingFeeSecurity, OfferingFeeTable


class S3CoverPage(WireModel):
    """S-3 cover-page fields (filer-category + rule checkboxes, state/EIN). No SIC code on the S-3 cover."""

    company_name: str
    registration_number: str | None
    state_of_incorporation: str | None
    ein: str | None

    # filer-category checkboxes (null when the box state cannot be read from the cover)
    is_large_accelerated_filer: bool | None
    is_accelerated_filer: bool | None
    is_non_accelerated_filer: bool | None
    is_smaller_reporting_company: bool | None
    is_emerging_growth_company: bool | None

    # rule checkboxes (edgar defaults each to False when unchecked/absent)
    is_rule_415: bool  # delayed/continuous offering (shelf) -- the defining S-3 box
    is_rule_462b: bool  # immediate-effectiveness additional-securities registration
    is_rule_462e: bool  # automatic shelf (WKSI); edgar also forces True when the form is an S-3ASR

    confidence: str  # extraction confidence: "low" / "medium" / "high"


# edgar S3OfferingType enum values (the .value strings)
S3OfferingTypeLiteral = Literal["universal_shelf", "resale", "debt", "auto_shelf", "unknown"]


class RegistrationS3Data(WireModel):
    """filing.obj() for an S-3/F-3 shelf registration (and /A) -- the edgar RegistrationS3, full fidelity."""

    kind: Literal["registration_s3"] = "registration_s3"
    form: str  # the specific variant: "S-3", "S-3/A", "S-3ASR", "S-3D", "F-3", "F-3ASR", ...
    company: str | None
    filing_date: str | None
    accession_number: str | None
    is_amendment: bool
    is_auto_shelf: bool  # automatic shelf (S-3ASR / WKSI): fees deferred under Rule 456(b)/457(r)
    offering_type: S3OfferingTypeLiteral  # universal-shelf / resale / debt / auto-shelf classification

    # convenience scalars (delegate to cover_page; on the wire for flat access)
    registration_number: str | None
    ein: str | None
    state_of_incorporation: str | None

    # fee-table convenience scalars + per-security breakdown
    total_offering: float | None  # from fee_table.total_offering_amount
    net_fee: float | None  # from fee_table.net_fee_due
    fee_deferred: bool  # whether fees are deferred (S-3ASR / Rule 456(b)/457(r))
    securities: list[OfferingFeeSecurity]  # from fee_table.securities (empty when no exhibit)

    cover_page: S3CoverPage  # always present (from_filing always builds it)
    fee_table: OfferingFeeTable | None  # Exhibit 107 fee table; null when the exhibit is absent or deferred

    # cross-entity fetch, served separately
    related_filings: None = None
    takedowns: None = None
