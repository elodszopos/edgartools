"""Wire models for /company/{id}/financials and /metrics (plan "Statement shape").

Statements are typed records with explicit per-period values - never dynamic period
columns. Values are RAW XBRL instance values (presentation=False); preferred_sign
ships per record so consumers can apply display signs themselves.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from app.models.common import ACCESSION_PATTERN, CIK_PATTERN, WireModel

FinancialsPeriod = Literal["annual", "quarterly"]
FinancialsView = Literal["raw", "standardized"]


class StatementPeriod(WireModel):
    key: str  # XBRL period key: duration_<start>_<end> | instant_<end>
    label: str
    period_type: Literal["duration", "instant"]
    period_start: date | None  # null for instant periods
    period_end: date
    period_months: int | None = Field(description="Approximate duration in whole months (3=quarter, 12=annual); null for instant periods.")


class StatementValue(WireModel):
    period_key: str
    value: float | str | None = Field(
        description="RAW XBRL instance value, never sign-adjusted for display: numeric fact, text fact (cover page, flags), or null when absent."
    )
    value_type: Literal["number", "text"] | None = Field(description="Discriminator for value: 'number', 'text', or null when value is null.")


class StatementRecord(WireModel):
    concept: str
    label: str
    standard_concept: str | None
    level: int = Field(description="Presentation indent depth within the statement hierarchy.")
    is_abstract: bool
    is_dimension: bool
    is_breakdown: bool
    dimension_axis: str | None
    dimension_member: str | None
    dimension_member_label: str | None
    dimension_label: str | None
    balance: Literal["debit", "credit"] | None = Field(
        description="XBRL balance attribute of the concept; with weight, determines how the value aggregates."
    )
    weight: float | None = Field(
        description="Calculation-arc weight toward the parent total (e.g. -1.0 subtracts); null when the concept is not in a calculation tree."
    )
    preferred_sign: float | None = Field(
        description="Display sign multiplier from the presentation linkbase: apply to values to reproduce SEC HTML display (e.g. -1.0 shows outflows as negative). Values ship raw."
    )
    parent_concept: str | None
    parent_abstract_concept: str | None
    unit: str | None = Field(description="Normalized unit: usd, shares, usdPerShare, number, ...")
    currency: str | None = Field(description="ISO 4217 code when the unit is monetary (incl. per-share); null for shares/pure numbers.")
    point_in_time: bool | None
    values: list[StatementValue]


class FinancialStatement(WireModel):
    periods: list[StatementPeriod]
    records: list[StatementRecord]


class FinancialsResponse(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    form: str
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    filing_date: date
    period_of_report: date | None
    superseded_by: str | None = Field(
        description="Accession of the latest later-filed amendment covering the same report period; null when this filing stands as-is."
    )
    period: FinancialsPeriod
    view: FinancialsView
    dimensions: bool
    amendments: bool  # request echo: whether amendments were eligible for selection
    income_statement: FinancialStatement | None
    balance_sheet: FinancialStatement | None
    cashflow_statement: FinancialStatement | None
    statement_of_equity: FinancialStatement | None
    comprehensive_income: FinancialStatement | None
    cover: FinancialStatement | None


class FilingProvenance(WireModel):
    form: str
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    filing_date: date
    period_of_report: date | None
    superseded_by: str | None = Field(
        description="Accession of the latest later-filed amendment covering the same report period; null when this filing stands as-is."
    )


class StitchedStatementRecord(WireModel):
    # stitched rows carry less metadata than single-filing rows (no dimensions);
    # concept-level attributes come from the first filing in the stitch that has them
    concept: str
    label: str
    standard_concept: str | None
    level: int = Field(description="Presentation indent depth within the statement hierarchy.")
    is_abstract: bool
    is_total: bool
    balance: Literal["debit", "credit"] | None = Field(
        description="XBRL balance attribute of the concept; with weight, determines how the value aggregates."
    )
    weight: float | None = Field(
        description="Calculation-arc weight toward the parent total (e.g. -1.0 subtracts); null when the concept is not in a calculation tree."
    )
    preferred_sign: float | None = Field(
        description="Display sign multiplier from the presentation linkbase: apply to values to reproduce SEC HTML display. Values ship raw."
    )
    unit: str | None = Field(description="Normalized unit: usd, shares, usdPerShare, number, ...")
    currency: str | None = Field(description="ISO 4217 code when the unit is monetary (incl. per-share); null for shares/pure numbers.")
    values: list[StatementValue]


class StitchedFinancialStatement(WireModel):
    periods: list[StatementPeriod]
    records: list[StitchedStatementRecord]


class MultiFinancialsResponse(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    period: FinancialsPeriod
    view: FinancialsView
    dimensions: bool
    amendments: bool  # request echo: whether amendments were eligible for selection
    # filings handed to the stitcher, newest first; periods reveal actual coverage
    # (the stitcher silently drops a filing whose XBRL fails to parse)
    filings: list[FilingProvenance]
    income_statement: StitchedFinancialStatement | None
    balance_sheet: StitchedFinancialStatement | None
    cashflow_statement: StitchedFinancialStatement | None
    statement_of_equity: StitchedFinancialStatement | None
    comprehensive_income: StitchedFinancialStatement | None


class TTMPeriod(WireModel):
    fiscal_year: int
    fiscal_period: str  # Q1-Q4; Q2-Q4 may be derived from YTD/annual facts
    # provenance of the fact backing this quarter; a derived quarter (e.g. Q4 =
    # FY - YTD9M) inherits the provenance of its source fact
    filing_date: date | None
    accession_number: str | None
    form_type: str | None


class TTMMetricModel(WireModel):
    concept: str
    label: str
    value: float
    unit: str
    as_of_date: date
    public_date: date | None = Field(
        description="Latest filing_date across the facts used in the calculation: when this data vintage was fully on file. The library may back a historical window with comparative facts re-reported in later filings, so this is the vintage's publication date, not necessarily the earliest date a TTM for the window was knowable. Null when fact provenance is missing."
    )
    periods: list[TTMPeriod]
    has_gaps: bool
    has_calculated_q4: bool
    warning: str | None


# wire reason a convenience TTM is unavailable. The first two mirror the library's
# TTMUnavailableReason (concept_absent / insufficient_quarters); "malformed" is the
# sidecar's own classification for a metric the library returns with no finite value
# or no unit. A unit test guards the library-sourced pair against drift.
TTMUnavailable = Literal["concept_absent", "insufficient_quarters", "malformed"]


class TTMConvenienceMetric(WireModel):
    # revenue/net_income are best-effort: rather than a bare null (which conflated
    # "concept not reported" with "couldn't compute"), carry the metric OR the reason.
    # Exactly one of metric / unavailable_reason is non-null.
    metric: TTMMetricModel | None
    unavailable_reason: TTMUnavailable | None = Field(
        description="Why metric is null: 'concept_absent' (no matching concept in the company facts), 'insufficient_quarters' (fewer than 4 consecutive quarters), or 'malformed' (library returned a non-finite value or no unit). Null when metric is present."
    )


class TTMResponse(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    as_of: str | None  # request echo: ISO date or YYYY-QN
    concept: str | None  # request echo
    # convenience metrics: always present; the wrapper says whether the TTM computed
    # or why it didn't (the explicit ?concept= path below fails loudly instead)
    revenue: TTMConvenienceMetric
    net_income: TTMConvenienceMetric
    metric: TTMMetricModel | None  # TTM for the requested concept


class FinancialMetrics(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    form: str
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    filing_date: date
    period_of_report: date | None
    superseded_by: str | None = Field(
        description="Accession of the latest later-filed amendment covering the same report period; null when this filing stands as-is."
    )
    period: FinancialsPeriod
    amendments: bool  # request echo: whether amendments were eligible for selection
    revenue: float | None
    operating_income: float | None
    net_income: float | None
    total_assets: float | None
    total_liabilities: float | None
    stockholders_equity: float | None
    current_assets: float | None
    current_liabilities: float | None
    operating_cash_flow: float | None
    capital_expenditures: float | None
    free_cash_flow: float | None
    shares_outstanding_basic: float | None
    shares_outstanding_diluted: float | None
    current_ratio: float | None
    debt_to_assets: float | None
