"""Typed `data` for the 424B prospectus family (edgar `Prospectus424B`).

`filing.obj()` returns one `Prospectus424B` for every 424B variant -- 424B1 (exchange offer / IPO),
424B2 (structured notes / bank debt), 424B3 (resale / rights), 424B4 (priced IPO / takedown), 424B5
(shelf takedown / ATM / PIPE), 424B7 (WKSI base update), 424B8 (supplement), and their /A amendments;
the specific form is the `form` field. The captured surface is the eager cover page plus the lazily
table-extracted prospectus sections: pricing, offering terms, selling stockholders, structured-note
key terms (424B2), dilution, capitalization, underwriting, and the EX-FILING FEES XBRL exhibit.

The selling-stockholders / underwriting / dilution / capitalization legs reuse the shared
`offering.py` models (same edgar BaseModels the S-1/S-3 expose); the 424B-specific cover, pricing,
offering-terms, structured-note, and filing-fee shapes live here. The fee leg is edgar's XBRL
`FilingFeesData` (all-string, as-filed) -- DISTINCT from the S-1/S-3 `RegistrationFeeTable`
(`OfferingFeeTable`, parsed floats). Top-level convenience scalars (registration_number, ticker,
variant, offering_amount, offering_price, is_atm, is_preliminary, is_supplement) are included for
flat access. Cross-entity shelf navigation (lifecycle, shelf_registration, related_filings,
related_8k) is present as nullable fields set to None -- they require additional SEC fetches.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel
from app.models.forms.offering import (
    OfferingCapitalization,
    OfferingDilution,
    OfferingSellingStockholders,
    OfferingUnderwriting,
)


class Prospectus424BCoverPage(WireModel):
    """424B cover-page fields. Amounts/prices are as-filed strings (may be sentinels like
    "at-the-market" / "market-price"); the edgar float accessors are derived, not mirrored."""

    company_name: str
    registration_number: str | None  # 333-XXXXXX
    is_supplement: bool
    is_preliminary: bool
    is_atm: bool  # at-the-market offering
    rule_number: str | None  # e.g. "424(b)(5)"
    security_description: str | None
    offering_amount: str | None
    offering_price: str | None
    exchange_ticker: str | None
    base_prospectus_date: str | None  # date of the base prospectus a supplement attaches to


class Prospectus424BPricingColumn(WireModel):
    """One column of the pricing table (e.g. "Per Share" / "Total"); all cells as-filed strings."""

    column_label: str | None
    offering_price: str | None
    fee_or_discount: str | None
    proceeds: str | None


class Prospectus424BPricing(WireModel):
    """Pricing table (price / fee / proceeds). None for ATM and resale filings (no pricing grid)."""

    columns: list[Prospectus424BPricingColumn]
    fee_type: str | None  # "underwriting_discount" / "placement_agent_fees"
    is_percentage_price: bool
    raw_rows: list[list[str]]  # raw extracted rows, the fallback behind the parsed columns


class Prospectus424BOfferingTerms(WireModel):
    """Key-value terms from "The Offering" section; all values as-filed strings."""

    shares_offered: str | None
    pre_funded_warrants_offered: str | None
    warrants_offered: str | None
    use_of_proceeds_summary: str | None
    trading_symbol: str | None
    listing_exchange: str | None
    additional_terms: dict[str, str | None]  # extractor catch-all (subscription price, record date, ...)


class Prospectus424BStructuredNote(WireModel):
    """Structured-note key terms (424B2 pricing supplements); all values as-filed strings."""

    issuer: str | None
    guarantor: str | None
    cusip: str | None
    pricing_date: str | None
    issue_date: str | None
    maturity_date: str | None
    underlying: str | None  # reference asset / index / market measure
    denominations: str | None
    term: str | None
    principal_amount: str | None
    upside_participation_rate: str | None
    max_return: str | None
    threshold_value: str | None  # barrier / threshold level
    buffer_amount: str | None
    coupon_rate: str | None
    coupon_frequency: str | None
    additional_terms: dict[str, str | None]  # extractor catch-all, accumulated across key-terms tables


class Prospectus424BFilingFeeRow(WireModel):
    """One security row of the EX-FILING FEES XBRL exhibit; all cells as-filed strings."""

    security_type: str | None
    security_title: str | None
    max_aggregate_offering_price: str | None
    fee_rate: str | None
    fee_amount: str | None
    fee_rule: str | None


class Prospectus424BFilingFees(WireModel):
    """EX-FILING FEES XBRL exhibit (Rule 408, 2022+). Always present; check `has_exhibit` -- when
    False every other field is null/empty (no exhibit on ~all 424B1/B4, ~half of 424B2/B5). Amounts
    are as-filed XBRL strings, NOT the parsed-float OfferingFeeTable the S-1/S-3 fee_table uses."""

    has_exhibit: bool
    exhibit_url: str | None
    form_type: str | None
    registration_file_number: str | None
    total_offering_amount: str | None
    total_fee_amount: str | None
    offering_rows: list[Prospectus424BFilingFeeRow]
    is_final_prospectus: bool  # ffd:FnlPrspctsFlg


# edgar OfferingType enum values (the .value strings); 424B7 is hardcoded to base_prospectus_update
Prospectus424BOfferingType = Literal[
    "firm_commitment",
    "atm",
    "best_efforts",
    "pipe_resale",
    "rights_offering",
    "exchange_offer",
    "structured_note",
    "debt_offering",
    "base_prospectus_update",
    "unknown",
]


class Prospectus424BData(WireModel):
    """filing.obj() for a 424B prospectus (any variant, and /A) -- the edgar Prospectus424B."""

    kind: Literal["prospectus_424b"] = "prospectus_424b"
    form: str  # the specific variant: "424B5", "424B2", "424B4/A", ...
    company: str | None
    filing_date: str | None
    accession_number: str | None
    is_amendment: bool
    amendment_number: int | None
    offering_type: Prospectus424BOfferingType  # classified; 424B7 always base_prospectus_update

    # convenience scalars (delegate to cover_page; on the wire for flat access)
    registration_number: str | None
    ticker: str | None  # exchange ticker from cover page
    variant: str | None  # form with /A stripped (e.g. "424B5")
    offering_amount: str | None  # as-filed cover page string
    offering_price: str | None  # as-filed cover page string
    is_atm: bool  # at-the-market offering
    is_preliminary: bool
    is_supplement: bool

    cover_page: Prospectus424BCoverPage  # always present (from_filing always builds it)

    # lazily table-extracted prospectus sections; None when the section/table is absent
    pricing: Prospectus424BPricing | None
    offering_terms: Prospectus424BOfferingTerms | None
    selling_stockholders: OfferingSellingStockholders | None  # shared offering.py model (resale tables)
    structured_note_terms: Prospectus424BStructuredNote | None  # 424B2 only
    dilution: OfferingDilution | None  # shared offering.py model
    capitalization: OfferingCapitalization | None  # shared offering.py model
    underwriting: OfferingUnderwriting | None  # shared offering.py model
    filing_fees: Prospectus424BFilingFees  # always present; has_exhibit gates the rest

    # cross-entity fetch, served separately
    related_filings: None = None
    related_8k: None = None
    shelf_registration: None = None
    lifecycle: None = None
