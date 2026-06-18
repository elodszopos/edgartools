"""Financials -> wire conversion (plan "Statement shape").

Statements come from Statement.to_dataframe(presentation=False) - raw instance values,
standardized labels per the view param. Period columns are unpivoted into typed
values[] records keyed by XBRL period key via df.attrs["period_columns"], the
column -> (period_key, period_label) mapping the library stamps at DataFrame build -
no column-name parsing here; a missing stamp raises KeyError loudly.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import pandas as pd
from edgar.financials import Financials
from edgar.xbrl.periods import determine_periods_to_display
from edgar.xbrl.presentation import StatementView
from edgar.xbrl.statements import Statement, StatementValidationError

from app.cik import pad_cik
from app.models.financials import (
    FilingProvenance,
    FilingXBRLResponse,
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
    from edgar.xbrl.stitching.xbrls import ParseOutcome as XBRLParseOutcome
    from edgar.xbrl.xbrl import XBRL


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


_METADATA_COLUMNS = frozenset(
    {
        "concept",
        "label",
        "standard_concept",
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
        "unit",
        "point_in_time",
    }
)


def _build_period_columns(
    stmt: Statement,
    df: pd.DataFrame,
) -> dict[str, tuple[str, str]]:
    """Reconstruct the column -> (period_key, period_label) map.

    The DataFrame's non-metadata columns are the period columns, in the same order
    as determine_periods_to_display. Zip them to get the mapping.
    """
    statement_type = stmt.canonical_type if stmt.canonical_type else stmt.role_or_type
    periods_to_display = determine_periods_to_display(stmt.xbrl, statement_type)
    data_columns = [c for c in df.columns if c not in _METADATA_COLUMNS]
    mapping: dict[str, tuple[str, str]] = {}
    for col, (period_key, period_label) in zip(data_columns, periods_to_display):
        mapping.setdefault(col, (period_key, period_label))
    return mapping


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

    column_to_period = _build_period_columns(stmt, df)
    period_columns = list(column_to_period)

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


def filing_xbrl_response(filing: Filing, xbrl: XBRL, *, view: FinancialsView, dimensions: bool) -> FilingXBRLResponse:
    """Single filing's XBRL statements, addressed by accession. Reuses the single-filing
    _statement shaping; the statements come straight off xbrl.statements (the same objects
    Financials delegates to), so /filing/{accession}/xbrl and /financials agree on a filing."""
    standard = view == "standardized"
    stmts = xbrl.statements
    return FilingXBRLResponse(
        cik=pad_cik(filing.cik),
        company=to_str(filing.company),
        form=filing.form,
        accession_number=filing.accession_no,
        filing_date=to_date(filing.filing_date),  # pyright: ignore[reportArgumentType] - filings always carry a date
        period_of_report=to_date(filing.period_of_report),
        view=view,
        dimensions=dimensions,
        income_statement=_statement(stmts.income_statement(), standard=standard, dimensions=dimensions),
        balance_sheet=_statement(stmts.balance_sheet(), standard=standard, dimensions=dimensions),
        cashflow_statement=_statement(stmts.cashflow_statement(), standard=standard, dimensions=dimensions),
        statement_of_equity=_statement(stmts.statement_of_equity(), standard=standard, dimensions=dimensions),
        comprehensive_income=_statement(stmts.comprehensive_income(), standard=standard, dimensions=dimensions),
        cover=_statement(stmts.cover_page(), standard=standard, dimensions=dimensions),
    )


def _resolve_preferred_sign(preferred_signs: dict[str, object]) -> tuple[float | None, bool]:
    """Collapse a concept's per-period preferred_signs to one display sign.

    The sign is concept-level, fanned out per period by the stitcher. Edgar no longer
    raises on variance (that crashed /financials/multi); instead, if periods/filings
    disagree (>1 distinct sign) there is no single correct sign, so surface it as
    ambiguous (sign null) rather than silently keeping an arbitrary first-seen pick.
    """
    distinct = {sign for sign in preferred_signs.values() if sign is not None}
    if len(distinct) > 1:
        return None, True
    return (to_float(next(iter(distinct))) if distinct else None), False


def _stitched_statement(stmt: StitchedStatement | None) -> StitchedFinancialStatement | None:
    """Build the wire statement from statement_data (the stitcher's public output).

    Unlike single-filing statements (which force the to_dataframe column-name
    mirroring), stitched line items key every value by its XBRL period id directly -
    no name mapping, no drift risk.
    """
    if stmt is None:
        return None
    sd = stmt.statement_data
    period_tuples = sd["periods"]  # [(period_id, label), ...]
    period_ids = [pid for pid, _ in period_tuples]
    periods = [_statement_period(pid, label) for pid, label in period_tuples]
    records = []
    for item in sd["statement_data"]:
        values_dict = item.get("values", {})
        preferred_sign, sign_ambiguous = _resolve_preferred_sign(item.get("preferred_signs", {}))
        records.append(
            StitchedStatementRecord(
                concept=str(item.get("concept", "")),
                label=str(item.get("label", "")),
                standard_concept=_opt_str(item.get("standard_concept")),
                level=_require_int(item.get("level", 0)),
                is_abstract=bool(item.get("is_abstract", False)),
                is_total=bool(item.get("is_total", False)),
                balance=_balance(item.get("balance")),
                weight=to_float(item.get("weight")),
                preferred_sign=preferred_sign,
                sign_ambiguous=sign_ambiguous,
                unit=_opt_str(item.get("unit")),
                currency=_currency(_opt_str(item.get("unit"))),
                values=[_statement_value(pid, values_dict.get(pid)) for pid in period_ids],
            )
        )
    return StitchedFinancialStatement(periods=periods, records=records)


def _filing_provenance_list(
    filings: Sequence[Filing],
    parse_outcomes: Sequence[XBRLParseOutcome],
    superseded_by: dict[str, str | None],
) -> list[FilingProvenance]:
    """Provenance for every filing handed to the stitcher, flagged parsed/failed.

    XBRLS.from_filings emits one outcome per input filing; correlate by accession so a
    filing whose XBRL failed to parse stays in the list flagged parsed=false (carrying the
    library's error) instead of vanishing from the stitched set. A missing outcome means
    the input list and parse_outcomes disagree - a contract break - so fail loud, like a
    missing superseded_by key.
    """
    outcomes = {outcome.accession_number: outcome for outcome in parse_outcomes}
    provenance: list[FilingProvenance] = []
    for filing in filings:
        outcome = outcomes[filing.accession_no]  # missing key = stitcher/input drift, fail loud
        provenance.append(
            FilingProvenance(
                form=filing.form,
                accession_number=filing.accession_no,
                filing_date=to_date(filing.filing_date),  # pyright: ignore[reportArgumentType] - filings always carry a date
                period_of_report=to_date(filing.period_of_report),
                parsed=outcome.parsed,
                parse_error=outcome.error,
                superseded_by=superseded_by[filing.accession_no],  # missing key = router bug, fail loud
            )
        )
    return provenance


def multi_financials_response(
    company: Company,
    filings: list[Filing],
    *,
    period: FinancialsPeriod,
    view: FinancialsView,
    dimensions: bool,
    amendments: bool,
    superseded_by: dict[str, str | None],  # accession -> superseding /A accession (router-computed)
    parse_outcomes: Sequence[XBRLParseOutcome],  # one per input filing (XBRLS.from_filings), keyed by accession
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
        filings=_filing_provenance_list(filings, parse_outcomes, superseded_by),
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
