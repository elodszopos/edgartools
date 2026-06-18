"""Typed `data` for the SEC beneficial-ownership schedules (SC 13D / SC 13G).

edgar backs these with two distinct objects (`Schedule13D`, `Schedule13G`) that SHARE the cover-page
nested types (reporting persons, issuer, security, signatures) but carry structurally different
narrative `items` (13D: 7 free-text items incl. the activist Item 4 purpose; 13G: 10 mostly-boolean
items). So two `kind`s -- `sc13d`, `sc13g` -- over one shared set of nested models.

Two regimes: filings on/after the SEC structured-XML mandate (2024-12-18) parse to full numerics;
older HTML-only filings yield `has_structured_data=False` with `total_shares`/`total_percent` null
and only the header identities recovered (reporting persons may be empty). The flag is the signal.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import Address, WireModel


class BeneficialOwner(WireModel):
    """One reporting person from the cover page (joint filers -> multiple).

    13G never carries the person CIK on the cover page (always null); 13D usually does."""

    cik: str | None  # as-filed, not zero-padded; null on 13G and on 13D no-CIK filers
    name: str
    citizenship: str | None
    sole_voting_power: int
    shared_voting_power: int
    sole_dispositive_power: int
    shared_dispositive_power: int
    aggregate_amount: int
    percent_of_class: float
    type_of_reporting_person: str | None  # SEC code: IN, OO, PN, HC, ...
    fund_type: str | None
    comment: str | None
    member_of_group: str | None  # "a" group member (joint filer) / "b" separate filer
    is_aggregate_exclude_shares: bool
    no_cik: bool


class Schedule13Issuer(WireModel):
    """The subject company whose securities are reported."""

    cik: str | None  # as-filed, not zero-padded
    name: str | None
    cusip: str | None
    address: Address | None


class Schedule13Security(WireModel):
    title: str | None
    cusip: str | None


class Schedule13Signature(WireModel):
    reporting_person: str | None
    signature: str | None
    title: str | None
    date: str | None  # as-filed MM/DD/YYYY string


class Schedule13DItems(WireModel):
    """13D narrative items 1-7 (Item 4, purpose of transaction, is the activist signal)."""

    item1_security_title: str | None
    item1_issuer_name: str | None
    item1_issuer_address: str | None
    item2_filing_persons: str | None
    item2_business_address: str | None
    item2_principal_occupation: str | None
    item2_convictions: str | None
    item2_citizenship: str | None
    item3_source_of_funds: str | None
    item4_purpose_of_transaction: str | None
    item5_percentage_of_class: str | None
    item5_number_of_shares: str | None
    item5_transactions: str | None
    item5_shareholders: str | None
    item5_date_5pct_ownership: str | None
    item6_contracts: str | None
    item7_exhibits: str | None


class Schedule13GItems(WireModel):
    """13G items 1-10 (mostly not-applicable flags + the Item 4 ownership block)."""

    item1_issuer_name: str | None
    item1_issuer_address: str | None
    item2_filer_names: str | None
    item2_filer_addresses: str | None
    item2_citizenship: str | None
    item3_not_applicable: bool
    item4_amount_beneficially_owned: str | None
    item4_percent_of_class: str | None
    item4_sole_voting: str | None
    item4_shared_voting: str | None
    item4_sole_dispositive: str | None
    item4_shared_dispositive: str | None
    item5_not_applicable: bool
    item5_ownership_5pct_or_less: str | None
    item6_not_applicable: bool
    item7_not_applicable: bool
    item8_not_applicable: bool
    item9_not_applicable: bool
    item10_certification: str | None


class Schedule13DData(WireModel):
    """filing.obj() for SC 13D - active (control-intent) 5%+ beneficial ownership."""

    kind: Literal["sc13d"] = "sc13d"
    issuer: Schedule13Issuer
    security: Schedule13Security
    reporting_persons: list[BeneficialOwner]
    items: Schedule13DItems
    signatures: list[Schedule13Signature]
    event_date: str | None  # date_of_event, as-filed MM/DD/YYYY
    date_of_event: str | None  # same value as event_date (edgar exposes both names)
    filing_date: str | None  # ISO date from the filing header
    previously_filed: bool
    is_amendment: bool
    amendment_number: int | None  # parsed "Amendment No. N"; null when the /A has no embedded number
    # False for pre-2024-12-18 HTML-only filings: totals are null and persons may be empty
    has_structured_data: bool
    total_shares: int | None  # max() across overlapping group owners; null when not structured
    total_percent: float | None


class Schedule13GData(WireModel):
    """filing.obj() for SC 13G - passive (institutional, no control intent) 5%+ ownership."""

    kind: Literal["sc13g"] = "sc13g"
    issuer: Schedule13Issuer
    security: Schedule13Security
    reporting_persons: list[BeneficialOwner]
    items: Schedule13GItems
    signatures: list[Schedule13Signature]
    event_date: str | None
    date_of_event: str | None  # same value as event_date (edgar exposes both names)
    filing_date: str | None  # ISO date from the filing header
    rule_designation: str | None  # e.g. "Rule 13d-1(b)" institutional / "Rule 13d-1(d)" exempt
    is_passive_investor: bool  # always True for 13G
    is_amendment: bool
    amendment_number: int | None
    has_structured_data: bool
    total_shares: int | None
    total_percent: float | None
