"""Typed `data` for the proxy-statement family (DEF 14A and every 14A variant).

`filing.obj()` returns one edgar `ProxyStatement` for the whole PROXY_FORMS set, so all
variants share this model; the specific form is the `form` field. Two data legs are captured:
the XBRL pay-vs-performance / governance facts (ecd: + dei: concepts) and the HTML-extracted
compensation tables (summary comp, director comp, beneficial ownership, audit fees, CEO pay
ratio, voting proposals). edgar exposes several tables as DataFrames whose columns are
documented + stable; the converter unpivots them to the typed rows below (U31 statement
precedent). `season` (a cross-entity proxy-season scan) is excluded by the lazy-property policy.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel


class ProxyVotingProposal(WireModel):
    number: int
    description: str
    board_recommendation: str | None  # "FOR" / "AGAINST" / "ABSTAIN" / null
    proposal_type: str  # e.g. "company_proposal" / "shareholder_proposal"


class ProxyCeoPayRatio(WireModel):
    ceo_compensation: float | None
    median_employee_compensation: float | None
    ratio: int | None  # integer ratio, e.g. 533 == 533:1


class ProxySummaryCompRow(WireModel):
    """One executive-year row of the Summary Compensation Table (Item 402(c))."""

    name: str | None
    title: str | None
    year: int | None
    salary: float | None
    bonus: float | None
    stock_awards: float | None
    option_awards: float | None
    non_equity_incentive: float | None
    pension_change: float | None
    other_compensation: float | None
    total: float | None


class ProxyDirectorCompRow(WireModel):
    """One non-employee-director row of the Director Compensation Table (Item 402(k))."""

    name: str | None
    fees_earned: float | None
    stock_awards: float | None
    option_awards: float | None
    non_equity_incentive: float | None
    pension_change: float | None
    other_compensation: float | None
    total: float | None


class ProxyBeneficialOwner(WireModel):
    """One holder row of the beneficial-ownership table (Item 403)."""

    holder_name: str | None
    holder_type: str | None  # "5pct_holder" / "director_officer" / "group"
    shares: float | None
    percent_of_class: float | None


class ProxyAuditFees(WireModel):
    """Auditor fee disclosure (current vs prior year)."""

    auditor_name: str | None
    current_year: int | None
    prior_year: int | None
    audit_fees_current: float | None
    audit_fees_prior: float | None
    audit_related_current: float | None
    audit_related_prior: float | None
    tax_fees_current: float | None
    tax_fees_prior: float | None
    other_fees_current: float | None
    other_fees_prior: float | None
    total_current: float | None
    total_prior: float | None


class ProxyExecCompRow(WireModel):
    """One fiscal year of the executive-compensation time series (XBRL ecd: PEO/NEO totals)."""

    fiscal_year_end: str | None
    peo_total_comp: float | None
    peo_actually_paid_comp: float | None
    neo_avg_total_comp: float | None
    neo_avg_actually_paid_comp: float | None


class ProxyPvpRow(WireModel):
    """One fiscal year of pay-vs-performance metrics (XBRL ecd: facts)."""

    fiscal_year_end: str | None
    peo_actually_paid_comp: float | None
    neo_avg_actually_paid_comp: float | None
    total_shareholder_return: float | None
    peer_group_tsr: float | None
    net_income: float | None
    company_selected_measure_value: float | None


class ProxyAwardCloseToMnpi(WireModel):
    """One equity-award grant made within 4 business days of MNPI disclosure (Item 402(x))."""

    grant_date: str | None
    executive: str | None
    award_type: str | None
    exercise_price: float | None
    grant_date_fair_value: float | None
    underlying_securities: float | None
    market_price_change_pct: float | None


class ProxyNamedExecutive(WireModel):
    """An individual NEO when the pay-vs-performance table is dimensionally tagged per executive."""

    name: str | None
    member_id: str | None
    role: str | None  # PEO / NEO / ...
    total_comp: float | None
    actually_paid_comp: float | None
    fiscal_year_end: str | None


class ProxyData(WireModel):
    """filing.obj() for the DEF 14A / 14A family - the edgar ProxyStatement object, full fidelity."""

    kind: Literal["proxy"] = "proxy"
    form: str  # the specific variant: "DEF 14A", "DEFM14A", "DEFC14A", "PRE 14A", "DFAN14A", ...
    filing_date: str | None
    company_name: str | None
    cik: str | None  # proxy.cik as filed (not zero-padded by edgar) -> no CIK_PATTERN
    accession_number: str | None
    has_xbrl: bool  # whether the filing carries the ecd: pay-vs-performance XBRL block

    # pay-vs-performance / SCT headline scalars (most-recent year, from XBRL ecd: facts)
    fiscal_year_end: str | None
    peo_name: str | None  # principal executive officer (CEO) name
    peo_total_comp: float | None
    peo_actually_paid_comp: float | None
    neo_avg_total_comp: float | None
    neo_avg_actually_paid_comp: float | None
    total_shareholder_return: float | None
    peer_group_tsr: float | None
    net_income: float | None
    company_selected_measure: str | None
    company_selected_measure_value: float | None
    performance_measures: list[str]

    # governance flags (Item 402(x) award-timing + insider-trading-policy XBRL booleans)
    insider_trading_policy_adopted: bool | None
    award_timing_mnpi_considered: bool | None
    award_dates_predetermined: bool | None
    mnpi_disclosure_timed_for_comp_value: bool | None
    has_individual_executive_data: bool

    # structured tables (typed rows; empty list when the section is absent from the filing)
    executive_compensation: list[ProxyExecCompRow]  # 5-year XBRL time series
    pay_vs_performance: list[ProxyPvpRow]  # 5-year XBRL metrics
    awards_close_to_mnpi: list[ProxyAwardCloseToMnpi]
    named_executives: list[ProxyNamedExecutive]
    summary_compensation_table: list[ProxySummaryCompRow]  # HTML-extracted
    director_compensation_table: list[ProxyDirectorCompRow]  # HTML-extracted
    beneficial_ownership: list[ProxyBeneficialOwner]  # HTML-extracted
    voting_proposals: list[ProxyVotingProposal]  # HTML-extracted
    ceo_pay_ratio: ProxyCeoPayRatio | None  # HTML-extracted; null when not disclosed (SRC/EGC exempt)
    audit_fees: ProxyAuditFees | None  # HTML-extracted; null when the section is not found

    # cross-entity fetch, served separately
    season: None = None  # ProxySeason via Company.proxy_season scan
