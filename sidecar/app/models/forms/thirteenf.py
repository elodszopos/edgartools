"""Typed `data` for SEC Form 13F (institutional investment-manager holdings reports).

edgar backs the whole 13F family - 13F-HR (holdings report), 13F-NT (notice that an affiliated
manager reports the holdings), 13F-CTR (combination), plus the /A amendments - with one
`ThirteenF` object, so one `kind` (`form13f`); the `form` field distinguishes the variant.
A 13F-HR carries the information table; a 13F-NT does not (`has_holdings` False, `holdings`
empty) but still parses the cover/summary/signature.

`holdings` is the DISAGGREGATED information table - one row per security per reporting manager
(edgar's `infotable`), full fidelity incl. per-row InvestmentDiscretion, OtherManager and the
voting-authority splits. The aggregated one-row-per-security view (edgar's `holdings` property)
is a CUSIP+put/call groupby derivable from these rows client-side, so it is not mirrored.
Values are whole dollars: edgar scales pre-2023 thousands-unit filings x1000, so both holding
`value` and `total_value` are era-independent dollars.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.common import Address, WireModel


class ThirteenFOtherManager(WireModel):
    """An affiliated manager whose holdings are reported in this consolidated filing."""

    cik: str | None
    name: str | None
    file_number: str | None
    sequence_number: int | None


class ThirteenFFilingManager(WireModel):
    name: str | None
    address: Address | None


class ThirteenFCoverPage(WireModel):
    report_calendar_or_quarter: str | None
    report_type: str | None
    filing_manager: ThirteenFFilingManager | None
    other_managers: list[ThirteenFOtherManager]


class ThirteenFSummary(WireModel):
    other_included_managers_count: int | None
    total_value: float | None  # whole dollars, normalized (Decimal -> float per wire policy)
    total_holdings: int | None
    # the summary-page "other managers 2" block; distinct from the cover page's list
    other_managers: list[ThirteenFOtherManager]


class ThirteenFSignature(WireModel):
    name: str | None
    title: str | None
    phone: str | None
    signature: str | None
    city: str | None
    state_or_country: str | None
    date: str | None  # as-filed date string


class ThirteenFHolding(WireModel):
    """One disaggregated information-table row (a security as held via one reporting manager)."""

    issuer: str | None
    title_of_class: str | None
    cusip: str | None
    ticker: str | None  # CUSIP->ticker mapping; null when the CUSIP is unmapped
    value: int | None  # whole dollars (pre-2023 thousands already scaled x1000)
    shares_or_principal_amount: int | None
    shares_or_principal_type: str | None  # "Shares" | "Principal"
    put_call: str | None  # "Put" | "Call"; null for an ordinary long position
    investment_discretion: str | None
    other_manager: str | None  # the reporting-manager reference for this row (multi-manager filings)
    sole_voting_authority: int | None
    shared_voting_authority: int | None
    no_voting_authority: int | None


class Form13FData(WireModel):
    """filing.obj() for the 13F family - one institutional manager's quarterly holdings report."""

    kind: Literal["form13f"] = "form13f"
    form: str  # 13F-HR | 13F-HR/A | 13F-NT | 13F-NT/A | 13F-CTR | 13F-CTR/A
    report_period: date | None  # period-of-report end date
    is_amendment: bool
    has_holdings: bool  # has_infotable(): True only for 13F-HR/HR-A; False for notices
    # envelope metadata
    accession_number: str | None
    filing_date: str | None
    # summary scalars (also in the nested summary block; top-level for convenience)
    total_holdings: int | None
    total_value: float | None  # whole dollars, Decimal -> float per wire policy
    # the cover/summary/signature come from the parsed primary XML; all null for the rare
    # pre-2013 TXT-only filing that has no primary document
    cover_page: ThirteenFCoverPage | None
    summary: ThirteenFSummary | None
    signature: ThirteenFSignature | None
    additional_information: str | None
    holdings: list[ThirteenFHolding]  # disaggregated; empty for notices / unparsed TXT tables
    # convenience manager/signer accessors
    filing_signer_name: str | None
    filing_signer_title: str | None
    signer: str | None  # same as filing_signer_name (edgar alias)
    investment_manager: str | None  # filing manager name from cover page
    management_company_name: str | None
    manager_name: str | None  # deprecated alias for management_company_name
    # top-level other-managers (same as summary.other_managers; for parity)
    other_managers: list[ThirteenFOtherManager]
    # raw information-table content
    infotable_txt: str | None
    infotable_xml: str | None
