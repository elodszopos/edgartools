"""edgar `Prospectus497K` (497K summary prospectus) -> `Prospectus497KData`, explicit field-by-field.

497K has ZERO XBRL; every cell is HTML-table parsed by edgar. Share-class fee rows and the $10K
expense example come off `obj.share_classes` (edgar `ShareClassFees`); the average-annual-returns rows
are read from the backing `obj._performance_returns` list -- the public `performance` DataFrame is a
lossy view that drops `inception_date`. Parsed Decimal cells cross as floats (the U53a rule),
expense-example dollars as ints. `form` is taken from the source filing (the object exposes no .form);
`prospectus_date` is the as-filed date text, kept as a string (not ISO, so never `to_date`). The
derived convenience members (tickers / class_ids / num_share_classes) and the DataFrame views are not
mapped (they duplicate data already present in the share_classes list).
"""

from __future__ import annotations

from decimal import Decimal

from edgar.funds.prospectus497k import (
    PerformanceReturn,
    Prospectus497K,
    ShareClassFees,
)

from app.cik import pad_cik
from app.models.forms.prospectus_497k import (
    Prospectus497KData,
    Prospectus497KPerformanceReturn,
    Prospectus497KQuarterReturn,
    Prospectus497KShareClass,
)
from app.serialize import to_float, to_int, to_str


def _share_class(sc: ShareClassFees) -> Prospectus497KShareClass:
    return Prospectus497KShareClass(
        class_name=to_str(sc.class_name),
        ticker=to_str(sc.ticker),
        class_id=to_str(sc.class_id),
        max_sales_load=to_float(sc.max_sales_load),
        max_deferred_sales_load=to_float(sc.max_deferred_sales_load),
        redemption_fee=to_float(sc.redemption_fee),
        management_fee=to_float(sc.management_fee),
        twelve_b1_fee=to_float(sc.twelve_b1_fee),
        other_expenses=to_float(sc.other_expenses),
        acquired_fund_fees=to_float(sc.acquired_fund_fees),
        total_annual_expenses=to_float(sc.total_annual_expenses),
        fee_waiver=to_float(sc.fee_waiver),
        net_expenses=to_float(sc.net_expenses),
        expense_1yr=to_int(sc.expense_1yr),
        expense_3yr=to_int(sc.expense_3yr),
        expense_5yr=to_int(sc.expense_5yr),
        expense_10yr=to_int(sc.expense_10yr),
    )


def _performance_return(pr: PerformanceReturn) -> Prospectus497KPerformanceReturn:
    return Prospectus497KPerformanceReturn(
        label=to_str(pr.label),
        section=to_str(pr.section),
        return_1yr=to_float(pr.return_1yr),
        return_5yr=to_float(pr.return_5yr),
        return_10yr=to_float(pr.return_10yr),
        return_since_inception=to_float(pr.return_since_inception),
        inception_date=to_str(pr.inception_date),
    )


def _quarter(q: tuple[Decimal, str] | None) -> Prospectus497KQuarterReturn | None:
    if q is None:
        return None
    pct, date_text = q
    return Prospectus497KQuarterReturn(return_pct=to_float(pct), date=to_str(date_text))


def prospectus_497k_data(obj: Prospectus497K) -> Prospectus497KData:
    filing = obj.filing
    cik = to_str(obj.cik)
    return Prospectus497KData(
        form=to_str(filing.form) if filing is not None else None,
        cik=pad_cik(cik) if cik else None,
        num_share_classes=obj.num_share_classes,
        tickers=list(obj.tickers),
        class_ids=list(obj.class_ids),
        fund_name=to_str(obj.fund_name),
        prospectus_date=to_str(obj.prospectus_date),
        investment_objective=to_str(obj.investment_objective),
        portfolio_turnover=to_float(obj.portfolio_turnover),
        portfolio_managers=[s for m in obj.portfolio_managers if (s := to_str(m)) is not None],
        series_id=to_str(obj.series_id),
        share_classes=[_share_class(sc) for sc in obj.share_classes],
        performance_returns=[_performance_return(pr) for pr in obj._performance_returns],
        best_quarter=_quarter(obj.best_quarter),
        worst_quarter=_quarter(obj.worst_quarter),
    )
