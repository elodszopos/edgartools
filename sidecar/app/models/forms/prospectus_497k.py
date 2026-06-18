"""Typed `data` for the 497K summary prospectus (edgar `Prospectus497K`).

Form 497K is the SEC-mandated summary prospectus for mutual funds / ETFs (Rule 498). It has ZERO XBRL
-- every structured field is HTML-table parsed by edgar -- and one `Prospectus497K` backs the form
(+/A). Fund identity (fund_name / series_id) replaces the issuer/company scalars of the equity
prospectus family; the envelope still carries the registrant cik / company / accession, so those are
not duplicated here. Fees and the $10K expense example are one `Prospectus497KShareClass` per share
class; the average-annual-returns rows mirror edgar's `PerformanceReturn`.

`performance_returns` is read from edgar's backing list, NOT from the public `performance` DataFrame:
that DataFrame is a lossy view (it drops `inception_date`). The convenience derivations edgar layers on
top -- `tickers` / `class_ids` (lists pulled off the share classes), `num_share_classes` (a length),
and the `fees` / `expense_example` DataFrame views (rows already captured in `share_classes`) -- are
not mapped (they duplicate data already present in the share_classes list). Parsed Decimal cells cross
the wire as floats (the U53a rule: floats where edgar parsed), the expense-example dollars as ints.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel


class Prospectus497KShareClass(WireModel):
    """Fee + $10K expense-example data for one share class (edgar `ShareClassFees`).

    Shareholder fees and annual-operating-expense ratios are parsed percentages (Decimal -> float);
    the expense-example cells are whole-dollar hypotheticals (int)."""

    class_name: str | None
    ticker: str | None
    class_id: str | None  # C000xxxxx
    max_sales_load: float | None
    max_deferred_sales_load: float | None
    redemption_fee: float | None
    management_fee: float | None
    twelve_b1_fee: float | None
    other_expenses: float | None
    acquired_fund_fees: float | None
    total_annual_expenses: float | None
    fee_waiver: float | None
    net_expenses: float | None
    expense_1yr: int | None
    expense_3yr: int | None
    expense_5yr: int | None
    expense_10yr: int | None


class Prospectus497KPerformanceReturn(WireModel):
    """One average-annual-returns row (edgar `PerformanceReturn`).

    Captured from the backing list rather than the public `performance` DataFrame, which drops
    `inception_date`. Returns are parsed percentages (Decimal -> float)."""

    label: str | None
    section: str | None  # share-class section header the row sits under
    return_1yr: float | None
    return_5yr: float | None
    return_10yr: float | None
    return_since_inception: float | None
    inception_date: str | None


class Prospectus497KQuarterReturn(WireModel):
    """Best / worst calendar-quarter return: edgar's (Decimal pct, date-text) tuple as a named pair."""

    return_pct: float | None
    date: str | None  # as-filed quarter-end text, e.g. "December 31, 2023"


class Prospectus497KData(WireModel):
    kind: Literal["prospectus_497k"] = "prospectus_497k"
    form: str | None  # 497K (+/A); the object has no .form, so this is the filing's form
    cik: str | None
    num_share_classes: int | None
    tickers: list[str]
    class_ids: list[str]
    fund_name: str | None
    prospectus_date: str | None  # as-filed date text (not ISO), e.g. "January 28, 2025"
    investment_objective: str | None
    portfolio_turnover: float | None  # percent of average portfolio value
    portfolio_managers: list[str]
    series_id: str | None  # S000xxxxx from the SGML header
    share_classes: list[Prospectus497KShareClass]
    performance_returns: list[Prospectus497KPerformanceReturn]
    best_quarter: Prospectus497KQuarterReturn | None
    worst_quarter: Prospectus497KQuarterReturn | None
