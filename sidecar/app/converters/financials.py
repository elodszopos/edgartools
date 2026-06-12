"""Financials -> wire conversion (plan "Statement shape").

Statements come from Statement.to_dataframe(presentation=False) - raw instance values,
standardized labels per the view param. Period columns are unpivoted into typed
values[] records via the same period-selection + column-naming logic the library uses
(determine_periods_to_display + the (FY)/(Qn)/(YTD) suffix rules in
edgar/xbrl/statements.py _build_dataframe_from_raw_data); the library exposes no public
period->column mapping, so the naming is mirrored here and every lookup is BY NAME -
a library rename breaks tests loudly instead of mislabeling periods.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Literal

import pandas as pd
from edgar.financials import Financials
from edgar.xbrl.periods import determine_periods_to_display
from edgar.xbrl.presentation import StatementView
from edgar.xbrl.statements import Statement, StatementValidationError

from app.cik import pad_cik
from app.models.financials import (
    FilingProvenance,
    FinancialMetrics,
    FinancialsPeriod,
    FinancialsResponse,
    FinancialStatement,
    FinancialsView,
    MultiFinancialsResponse,
    StatementPeriod,
    StatementRecord,
    StatementValue,
    StitchedFinancialStatement,
    StitchedStatementRecord,
    TTMMetricModel,
    TTMPeriod,
)
from app.serialize import to_bool, to_date, to_float, to_int, to_str

if TYPE_CHECKING:
    from edgar._filings import Filing
    from edgar.entity.core import Company
    from edgar.ttm.calculator import TTMMetric
    from edgar.xbrl.statements import StitchedStatement

# every non-period column to_dataframe(include_unit, include_point_in_time) can emit;
# the remaining columns are period values in determine_periods_to_display order
_METADATA_COLUMNS = frozenset(
    {
        "concept",
        "label",
        "standard_concept",
        "unit",
        "point_in_time",
        "level",
        "abstract",
        "dimension",
        "is_breakdown",
        "dimension_axis",
        "dimension_member",
        "dimension_member_label",
        "dimension_label",
        "balance",
        "weight",
        "preferred_sign",
        "parent_concept",
        "parent_abstract_concept",
    }
)


def _period_column_name(period_key: str, period_label: str, fiscal_year_end_month: int | None) -> str:
    # mirrors the column naming in Statement._build_dataframe_from_raw_data
    parts = period_key.split("_")
    if period_key.startswith("duration_") and len(parts) >= 3:
        start_date, end_date = parts[1], parts[2]
        name = end_date
        try:
            d0 = datetime.strptime(start_date, "%Y-%m-%d")
            d1 = datetime.strptime(end_date, "%Y-%m-%d")
            days = (d1 - d0).days
            if 80 <= days <= 100:
                if fiscal_year_end_month:
                    month_offset = (d1.month - fiscal_year_end_month - 1) % 12
                    quarter = f"Q{(month_offset // 3) + 1}"
                else:
                    month = d1.month
                    quarter = "Q1" if month <= 3 or month == 12 else "Q2" if month <= 6 else "Q3" if month <= 9 else "Q4"
                name = f"{end_date} ({quarter})"
            elif 175 <= days <= 285:
                name = f"{end_date} (YTD)"
            elif days > 350:
                name = f"{end_date} (FY)"
        except (ValueError, TypeError):
            pass
        return name
    if period_key.startswith("instant_") and len(parts) >= 2:
        return parts[1]
    return period_label


def _statement_period(period_key: str, period_label: str) -> StatementPeriod:
    parts = period_key.split("_")
    if period_key.startswith("duration_") and len(parts) >= 3:
        start, end = to_date(parts[1]), to_date(parts[2])
        months = round((end - start).days / 30.44) if start is not None and end is not None else None
        return StatementPeriod(
            key=period_key,
            label=period_label,
            period_type="duration",
            period_start=start,
            period_end=end,  # pyright: ignore[reportArgumentType] - key always carries the end date
            period_months=months,
        )
    if period_key.startswith("instant_") and len(parts) >= 2:
        return StatementPeriod(
            key=period_key,
            label=period_label,
            period_type="instant",
            period_start=None,
            period_end=to_date(parts[1]),  # pyright: ignore[reportArgumentType]
            period_months=None,
        )
    raise ValueError(f"unrecognized XBRL period key: {period_key!r}")


def _opt_str(raw: object) -> str | None:
    if raw is None or (not isinstance(raw, str) and bool(pd.isna(raw))):
        return None
    return to_str(str(raw))


def _require_int(raw: object) -> int:
    number = to_int(raw)
    if number is None:
        raise TypeError(f"expected an integer, got {raw!r}")
    return number


def _value(raw: object) -> float | str | None:
    """Raw instance value: numeric fact -> float, text fact -> str, missing -> null."""
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    return to_float(raw)


def _statement_value(period_key: str, raw: object) -> StatementValue:
    value = _value(raw)
    value_type: Literal["number", "text"] | None = None if value is None else ("text" if isinstance(value, str) else "number")
    return StatementValue(period_key=period_key, value=value, value_type=value_type)


def _balance(raw: object) -> Literal["debit", "credit"] | None:
    text = _opt_str(raw)
    if text is None:
        return None
    if text in ("debit", "credit"):
        return text
    raise TypeError(f"unexpected XBRL balance attribute: {text!r}")


_CURRENCY_UNIT = re.compile(r"^([a-z]{3})(?:PerShare)?$")


def _currency(unit: str | None) -> str | None:
    """ISO 4217 code for monetary units (usd -> USD, usdPerShare -> USD); null otherwise.

    Normalized units come from get_unit_display_name: 3-letter monetary codes and their
    PerShare variants are monetary; shares/number/perShare are not.
    """
    if unit is None:
        return None
    match = _CURRENCY_UNIT.match(unit)
    return match.group(1).upper() if match else None


def _statement(stmt: Statement | None, *, standard: bool, dimensions: bool) -> FinancialStatement | None:
    if stmt is None:
        return None
    view = StatementView.DETAILED if dimensions else StatementView.SUMMARY
    try:
        df = stmt.to_dataframe(
            standard=standard,
            view=view,
            include_unit=True,
            include_point_in_time=True,
            presentation=False,  # raw signs on the wire; preferred_sign ships per record
        )
    except StatementValidationError:
        return None
    if df is None or isinstance(df, str) or df.empty:
        return FinancialStatement(periods=[], records=[])

    xbrl = stmt.xbrl
    statement_type = stmt.canonical_type if stmt.canonical_type else stmt.role_or_type
    fiscal_year_end_month = (xbrl.entity_info or {}).get("fiscal_year_end_month")
    selected = determine_periods_to_display(xbrl, statement_type)

    # transition periods can collapse onto one column (library issue #582) - keep first
    column_to_period: dict[str, tuple[str, str]] = {}
    for period_key, period_label in selected:
        column = _period_column_name(period_key, period_label, fiscal_year_end_month)
        column_to_period.setdefault(column, (period_key, period_label))

    period_columns = [column for column in df.columns if column not in _METADATA_COLUMNS]
    unmapped = [column for column in period_columns if column not in column_to_period]
    if unmapped:
        raise RuntimeError(
            f"statement period columns {unmapped} have no period mapping for {statement_type}; "
            "the mirrored column-naming logic has drifted from edgar.xbrl.statements"
        )

    periods = [_statement_period(*column_to_period[column]) for column in period_columns]
    records = []
    for row in df.to_dict(orient="records"):
        unit = _opt_str(row.get("unit"))
        records.append(
            StatementRecord(
                concept=str(row["concept"]),
                label=str(row["label"]),
                standard_concept=_opt_str(row.get("standard_concept")),
                level=_require_int(row["level"]),
                is_abstract=bool(row["abstract"]),
                is_dimension=bool(row["dimension"]),
                is_breakdown=bool(row["is_breakdown"]),
                dimension_axis=_opt_str(row.get("dimension_axis")),
                dimension_member=_opt_str(row.get("dimension_member")),
                dimension_member_label=_opt_str(row.get("dimension_member_label")),
                dimension_label=_opt_str(row.get("dimension_label")),
                balance=_balance(row.get("balance")),
                weight=to_float(row.get("weight")),
                preferred_sign=to_float(row.get("preferred_sign")),
                parent_concept=_opt_str(row.get("parent_concept")),
                parent_abstract_concept=_opt_str(row.get("parent_abstract_concept")),
                unit=unit,
                currency=_currency(unit),
                point_in_time=to_bool(row.get("point_in_time")),
                values=[_statement_value(column_to_period[column][0], row.get(column)) for column in period_columns],
            )
        )
    return FinancialStatement(periods=periods, records=records)


def financials_response(
    company: Company,
    filing: Filing,
    financials: Financials,
    *,
    period: FinancialsPeriod,
    view: FinancialsView,
    dimensions: bool,
    amendments: bool,
    superseded_by: str | None,
) -> FinancialsResponse:
    standard = view == "standardized"
    return FinancialsResponse(
        cik=pad_cik(company.cik),
        company=to_str(company.display_name),
        form=filing.form,
        accession_number=filing.accession_no,
        filing_date=to_date(filing.filing_date),  # pyright: ignore[reportArgumentType] - filings always carry a date
        period_of_report=to_date(filing.period_of_report),
        superseded_by=superseded_by,
        period=period,
        view=view,
        dimensions=dimensions,
        amendments=amendments,
        income_statement=_statement(financials.income_statement(), standard=standard, dimensions=dimensions),
        balance_sheet=_statement(financials.balance_sheet(), standard=standard, dimensions=dimensions),
        cashflow_statement=_statement(financials.cashflow_statement(), standard=standard, dimensions=dimensions),
        statement_of_equity=_statement(financials.statement_of_equity(), standard=standard, dimensions=dimensions),
        comprehensive_income=_statement(financials.comprehensive_income(), standard=standard, dimensions=dimensions),
        cover=_statement(financials.cover(), standard=standard, dimensions=dimensions),
    )


def _stitched_statement(stmt: StitchedStatement | None) -> StitchedFinancialStatement | None:
    """Build the wire statement from the stitched statement's public accessors.

    Unlike single-filing statements (which force the to_dataframe column-name
    mirroring), stitched line items key every value by its XBRL period id directly -
    no name mapping, no drift risk.
    """
    if stmt is None:
        return None
    stitched_periods = stmt.stitched_periods
    period_ids = [period.period_id for period in stitched_periods]
    periods = [_statement_period(period.period_id, period.label) for period in stitched_periods]
    records = []
    for item in stmt.line_items():
        unit = _opt_str(item.unit)
        records.append(
            StitchedStatementRecord(
                concept=str(item.concept),
                label=str(item.label),
                standard_concept=_opt_str(item.standard_concept),
                level=_require_int(item.level),
                is_abstract=bool(item.is_abstract),
                is_total=bool(item.is_total),
                balance=_balance(item.balance),
                weight=to_float(item.weight),
                # concept-level sign; the stitcher guarantees per-period uniformity (raises otherwise)
                preferred_sign=to_float(item.preferred_sign),
                unit=unit,
                currency=_currency(unit),
                values=[_statement_value(period_id, item.period_values.get(period_id)) for period_id in period_ids],
            )
        )
    return StitchedFinancialStatement(periods=periods, records=records)


def multi_financials_response(
    company: Company,
    filings: list[Filing],
    *,
    period: FinancialsPeriod,
    view: FinancialsView,
    dimensions: bool,
    amendments: bool,
    superseded_by: dict[str, str | None],  # accession -> superseding /A accession (router-computed)
    income_statement: StitchedStatement | None,
    balance_sheet: StitchedStatement | None,
    cashflow_statement: StitchedStatement | None,
    statement_of_equity: StitchedStatement | None,
    comprehensive_income: StitchedStatement | None,
) -> MultiFinancialsResponse:
    return MultiFinancialsResponse(
        cik=pad_cik(company.cik),
        company=to_str(company.display_name),
        period=period,
        view=view,
        dimensions=dimensions,
        amendments=amendments,
        filings=[
            FilingProvenance(
                form=filing.form,
                accession_number=filing.accession_no,
                filing_date=to_date(filing.filing_date),  # pyright: ignore[reportArgumentType] - filings always carry a date
                period_of_report=to_date(filing.period_of_report),
                superseded_by=superseded_by[filing.accession_no],  # missing key = router bug, fail loud
            )
            for filing in filings
        ],
        income_statement=_stitched_statement(income_statement),
        balance_sheet=_stitched_statement(balance_sheet),
        cashflow_statement=_stitched_statement(cashflow_statement),
        statement_of_equity=_stitched_statement(statement_of_equity),
        comprehensive_income=_stitched_statement(comprehensive_income),
    )


def ttm_metric_model(metric: TTMMetric) -> TTMMetricModel:
    value = to_float(metric.value)
    if value is None:  # NaN/inf collapse to None in to_float; a TTM sum must be a real number
        raise TypeError(f"TTM value for {metric.concept} is not a finite number: {metric.value!r}")
    unit = to_str(metric.unit)
    if unit is None:
        raise TypeError(f"TTM metric for {metric.concept} carries no unit")
    # periods and period_facts are built from the same quarter window; drift = library bug
    periods = [
        TTMPeriod(
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            filing_date=to_date(fact.filing_date),
            accession_number=to_str(fact.accession),
            form_type=to_str(fact.form_type),
        )
        for (fiscal_year, fiscal_period), fact in zip(metric.periods, metric.period_facts, strict=True)
    ]
    filing_dates = [p.filing_date for p in periods]
    # the full TTM value is knowable only once every source fact is on file; any
    # missing provenance makes the latest-known date understate it -> null instead
    public_date = max(filing_dates) if filing_dates and all(d is not None for d in filing_dates) else None  # pyright: ignore[reportArgumentType]
    return TTMMetricModel(
        concept=metric.concept,
        label=metric.label,
        value=value,
        unit=unit,
        as_of_date=to_date(metric.as_of_date),  # pyright: ignore[reportArgumentType] - TTM windows always end on a date
        public_date=public_date,
        periods=periods,
        has_gaps=bool(metric.has_gaps),
        has_calculated_q4=bool(metric.has_calculated_q4),
        warning=_opt_str(metric.warning),
    )


def metrics_response(
    company: Company,
    filing: Filing,
    financials: Financials,
    *,
    period: FinancialsPeriod,
    amendments: bool,
    superseded_by: str | None,
) -> FinancialMetrics:
    metrics = financials.get_financial_metrics()
    return FinancialMetrics(
        cik=pad_cik(company.cik),
        company=to_str(company.display_name),
        form=filing.form,
        accession_number=filing.accession_no,
        filing_date=to_date(filing.filing_date),  # pyright: ignore[reportArgumentType]
        period_of_report=to_date(filing.period_of_report),
        superseded_by=superseded_by,
        period=period,
        amendments=amendments,
        revenue=to_float(metrics["revenue"]),
        operating_income=to_float(metrics["operating_income"]),
        net_income=to_float(metrics["net_income"]),
        total_assets=to_float(metrics["total_assets"]),
        total_liabilities=to_float(metrics["total_liabilities"]),
        stockholders_equity=to_float(metrics["stockholders_equity"]),
        current_assets=to_float(metrics["current_assets"]),
        current_liabilities=to_float(metrics["current_liabilities"]),
        operating_cash_flow=to_float(metrics["operating_cash_flow"]),
        capital_expenditures=to_float(metrics["capital_expenditures"]),
        free_cash_flow=to_float(metrics["free_cash_flow"]),
        shares_outstanding_basic=to_float(metrics["shares_outstanding_basic"]),
        shares_outstanding_diluted=to_float(metrics["shares_outstanding_diluted"]),
        current_ratio=to_float(metrics["current_ratio"]),
        debt_to_assets=to_float(metrics["debt_to_assets"]),
    )
