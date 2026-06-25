"""U57c converter: edgar.funds.ncsr.FundShareholderReport -> NcsrData, explicit field-by-field.

Upstream FundShareholderReport is single-fund: it flattens a whole trust's classes into one
`share_classes[]` and carries neither the SEC series grouping, the class C-ids, nor the per-cell
(horizon x sales-load) average-annual returns the wire shape needs. So this converter uses the object
only as the open-end-fund gate (a non-None obj proves the oef Inline XBRL is present) and recovers the
data from public API: the SGML header's SERIES-AND-CLASSES registry (authoritative series/class
identity + grouping, declaration order) and the oef XBRL facts (`filing.xbrl()` FactQuery), keyed by
class C-id off the oef:ClassAxis dimension.

Identity (series_id / fund_name / class_id / class_name / class_ticker) is as-filed SGML text. Figures
are oef facts: per-class expense ratio / expenses-paid / annual returns; the fund-level figures
(net_assets / portfolio_turnover / advisory_fees_paid / holdings_count) are filed dimensioned by
ClassAxis and unanimous within a series, so each is taken from the series' classes.
"""

from __future__ import annotations

from edgar.funds.ncsr import FundShareholderReport

from app.cik import pad_cik
from app.models.forms.ncsr import NcsrAnnualReturn, NcsrData, NcsrFund, NcsrShareClass
from app.serialize import to_float, to_int, to_str
from app.sgml_series import SeriesContract, parse_series_classes

# oef:ClassAxis member -> class C-id; SalesLoadAxis member that marks a without-load return cell
_CLASS_AXIS = "dim_oef_ClassAxis"
_SALES_LOAD_AXIS = "dim_oef_SalesLoadAxis"
_WITHOUT_LOAD_MEMBER = "oef:WithoutSalesLoadMember"

# per-class oef figures
_EXPENSE_RATIO = "oef:ExpenseRatioPct"
_EXPENSES_PAID = "oef:ExpensesPaidAmt"
_AVG_ANNUAL_RETURN = "oef:AvgAnnlRtrPct"

# fund-level figures, filed dimensioned by ClassAxis and unanimous within a series
_NET_ASSETS = "us-gaap:AssetsNet"
_PORTFOLIO_TURNOVER = "us-gaap:InvestmentCompanyPortfolioTurnover"
_ADVISORY_FEES = "oef:AdvisoryFeesPaidAmt"
_HOLDINGS_COUNT = "oef:HoldingsCount"


def _class_id(member: object) -> str | None:
    # member is `<filer-prefix>:C000000131Member`; strip the namespace prefix and the Member suffix
    if not isinstance(member, str) or not member:
        return None
    tail = member.rsplit(":", 1)[-1]
    if tail.endswith("Member"):
        tail = tail[: -len("Member")]
    return tail or None


def _scalar_by_class(facts, concept: str) -> dict[str, object]:
    # first numeric value per class C-id (fund-level concepts repeat the same value on every class)
    out: dict[str, object] = {}
    for row in facts.query().by_concept(concept, exact=True).execute():
        cid = _class_id(row.get(_CLASS_AXIS))
        if cid is None or cid in out:
            continue
        out[cid] = row.get("numeric_value")
    return out


def _returns_by_class(facts) -> dict[str, list[dict]]:
    # oef:AvgAnnlRtrPct rows per class C-id, document order preserved; undimensioned benchmark
    # (broad-based index) rows carry no ClassAxis and are dropped
    out: dict[str, list[dict]] = {}
    for row in facts.query().by_concept(_AVG_ANNUAL_RETURN, exact=True).execute():
        cid = _class_id(row.get(_CLASS_AXIS))
        if cid is None:
            continue
        out.setdefault(cid, []).append(row)
    return out


def _annual_return(row: dict) -> NcsrAnnualReturn:
    return NcsrAnnualReturn(
        period_start=to_str(row.get("period_start")),  # horizon start (1yr/5yr/10yr differ only here)
        period_end=to_str(row.get("period_end")),
        return_pct=to_float(row.get("numeric_value")),
        without_sales_load=row.get(_SALES_LOAD_AXIS) == _WITHOUT_LOAD_MEMBER,
    )


def _share_class(
    contract,
    ratios: dict[str, object],
    expenses: dict[str, object],
    returns: dict[str, list[dict]],
) -> NcsrShareClass:
    cid = contract.class_id
    return NcsrShareClass(
        class_id=to_str(contract.class_id),
        class_name=to_str(contract.class_name),
        class_ticker=to_str(contract.class_ticker),
        expense_ratio_pct=to_float(ratios.get(cid)),
        expenses_paid_amt=to_float(expenses.get(cid)),
        annual_returns=[_annual_return(r) for r in returns.get(cid, [])],
    )


def _first(figures: dict[str, object], class_ids: list[str | None]) -> object:
    for cid in class_ids:
        if cid is not None and figures.get(cid) is not None:
            return figures[cid]
    return None


def _fund(
    series: SeriesContract,
    net_assets: dict[str, object],
    turnover: dict[str, object],
    advisory: dict[str, object],
    holdings_count: dict[str, object],
    ratios: dict[str, object],
    expenses: dict[str, object],
    returns: dict[str, list[dict]],
) -> NcsrFund:
    class_ids = [c.class_id for c in series.classes]
    return NcsrFund(
        series_id=to_str(series.series_id),
        fund_name=to_str(series.series_name),
        net_assets=to_float(_first(net_assets, class_ids)),
        portfolio_turnover=to_float(_first(turnover, class_ids)),
        advisory_fees_paid=to_float(_first(advisory, class_ids)),
        holdings_count=to_int(_first(holdings_count, class_ids)),
        # oef:HoldingPctOfNav is never tagged by filers; holdings_count comes from oef:HoldingsCount but
        # the per-holding breakdown lives in unstructured HTML, not XBRL -- edgar returns [] here
        holdings=[],
        share_classes=[_share_class(c, ratios, expenses, returns) for c in series.classes],
    )


def ncsr_data(obj: FundShareholderReport) -> NcsrData:
    filing = obj.filing
    series = parse_series_classes(filing.header.text)
    facts = filing.xbrl().facts

    net_assets = _scalar_by_class(facts, _NET_ASSETS)
    turnover = _scalar_by_class(facts, _PORTFOLIO_TURNOVER)
    advisory = _scalar_by_class(facts, _ADVISORY_FEES)
    holdings_count = _scalar_by_class(facts, _HOLDINGS_COUNT)
    ratios = _scalar_by_class(facts, _EXPENSE_RATIO)
    expenses = _scalar_by_class(facts, _EXPENSES_PAID)
    returns = _returns_by_class(facts)

    funds = [_fund(s, net_assets, turnover, advisory, holdings_count, ratios, expenses, returns) for s in series]
    cik = to_str(obj.cik)
    return NcsrData(
        form=to_str(filing.form),
        cik=pad_cik(cik) if cik else None,
        fund_name=to_str(obj.fund_name),
        series_id=to_str(obj.series_id),
        net_assets=to_float(obj.net_assets),
        portfolio_turnover=to_float(obj.portfolio_turnover),
        report_type=to_str(obj.report_type),
        is_annual=bool(obj.is_annual),
        num_share_classes=sum(len(f.share_classes) for f in funds),
        funds=funds,
        share_classes=[sc for f in funds for sc in f.share_classes],
    )
