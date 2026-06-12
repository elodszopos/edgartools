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


class StatementValue(WireModel):
    period_key: str
    # raw instance value: numeric fact, text fact (cover page, flags), or absent
    value: float | str | None


class StatementRecord(WireModel):
    concept: str
    label: str
    standard_concept: str | None
    level: int
    is_abstract: bool
    is_dimension: bool
    is_breakdown: bool
    dimension_axis: str | None
    dimension_member: str | None
    dimension_member_label: str | None
    dimension_label: str | None
    balance: Literal["debit", "credit"] | None
    weight: float | None
    preferred_sign: float | None
    parent_concept: str | None
    parent_abstract_concept: str | None
    unit: str | None
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
    period: FinancialsPeriod
    view: FinancialsView
    dimensions: bool
    income_statement: FinancialStatement | None
    balance_sheet: FinancialStatement | None
    cashflow_statement: FinancialStatement | None
    statement_of_equity: FinancialStatement | None
    comprehensive_income: FinancialStatement | None
    cover: FinancialStatement | None


class FinancialMetrics(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    form: str
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    filing_date: date
    period_of_report: date | None
    period: FinancialsPeriod
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
