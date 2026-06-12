"""GET /company/{id}/financials (+ /metrics, /multi stitched, /ttm trailing-twelve-months)."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import date
from typing import TYPE_CHECKING, Annotated

from edgar._filings import Filing
from edgar.entity.core import ANNUAL_FINANCIAL_FORMS, QUARTERLY_FINANCIAL_FORMS, Company
from edgar.entity.filings import EntityFiling
from edgar.financials import Financials
from edgar.xbrl.presentation import StatementView
from edgar.xbrl.stitching.xbrls import XBRLS
from fastapi import APIRouter, HTTPException, Query

from app.cik import pad_cik
from app.converters.financials import (
    financials_response,
    metrics_response,
    multi_financials_response,
    ttm_metric_model,
)
from app.deps import lookup_company
from app.models.common import error_responses
from app.models.financials import (
    FinancialMetrics,
    FinancialsPeriod,
    FinancialsResponse,
    FinancialsView,
    MultiFinancialsResponse,
    TTMMetricModel,
    TTMResponse,
)
from app.serialize import to_date, to_str

if TYPE_CHECKING:
    from edgar.ttm.calculator import TTMMetric

router = APIRouter(responses=error_responses(404, 422, 429, 502))

_TTM_QUARTER_KEY = re.compile(r"^\d{4}-[Qq][1-4]$")

# the period -> form fallback chain, sourced from edgartools' public constants so the
# sidecar and Company.get_financials / get_quarterly_financials cannot drift apart; the
# filing is selected here (not via those methods) so the response can carry its provenance
_FORM_CHAIN: dict[str, tuple[str, ...]] = {
    "annual": ANNUAL_FINANCIAL_FORMS,
    "quarterly": QUARTERLY_FINANCIAL_FORMS,
}


def _latest_financials(company: Company, period: FinancialsPeriod, *, amendments: bool) -> tuple[Filing, Financials]:
    forms = _FORM_CHAIN[period]
    for form in forms:
        filing = company.get_filings(form=form, amendments=amendments, trigger_full_load=False).latest()
        if isinstance(filing, Filing):  # latest() with default n=1 yields one filing or None
            financials = Financials.extract(filing)
            if financials is None:  # filing exists but carries no XBRL data
                raise HTTPException(
                    status_code=404,
                    detail=f"latest {form} {filing.accession_no} has no XBRL financial data",
                )
            return filing, financials
    raise HTTPException(
        status_code=404,
        detail=f"no {period} filing ({'/'.join(forms)}) at SEC for CIK {pad_cik(company.cik)}",
    )


def _superseding_amendments(company: Company, filings: Sequence[Filing]) -> dict[str, str | None]:
    """accession -> accession of the latest later-filed /A covering the same report period.

    None means the filing stands as-is. Pure in-memory correlation: the company's
    submissions index is already loaded, so the amendment lookup costs no HTTP. A filing
    whose report period is unknown maps to None - there is no safe way to correlate it.
    """
    result: dict[str, str | None] = {}
    candidates_by_form: dict[str, list[dict[str, object]]] = {}
    for filing in filings:
        base_form = filing.form.removesuffix("/A")
        if base_form not in candidates_by_form:
            amendment_filings = company.get_filings(form=f"{base_form}/A", amendments=True, trigger_full_load=False)
            candidates_by_form[base_form] = amendment_filings.data.to_pylist()
        # EntityFiling carries the submissions reportDate in memory; the generic
        # period_of_report property would fetch the SGML header instead
        report_date = to_str(filing.report_date) if isinstance(filing, EntityFiling) else to_str(filing.period_of_report)
        filed = to_date(filing.filing_date)
        superseding = None
        if report_date is not None and filed is not None:
            matches = [
                row
                for row in candidates_by_form[base_form]
                if row["accession_number"] != filing.accession_no
                and to_str(row["reportDate"]) == report_date
                and to_date(row["filing_date"]) is not None
                # strictly later, or same-day with a higher accession (monotonic per filer)
                and (to_date(row["filing_date"]), row["accession_number"]) > (filed, filing.accession_no)  # pyright: ignore[reportOperatorIssue]
            ]
            if matches:
                latest = max(matches, key=lambda row: (to_date(row["filing_date"]), row["accession_number"]))  # pyright: ignore[reportArgumentType,reportCallIssue]
                superseding = str(latest["accession_number"])
        result[filing.accession_no] = superseding
    return result


@router.get("/company/{id}/financials")
def get_company_financials(
    id: str,
    period: FinancialsPeriod = "annual",
    view: FinancialsView = "standardized",
    dimensions: bool = False,
    amendments: bool = False,  # filing-selection policy: as-filed (false) vs restated (true)
) -> FinancialsResponse:
    company = lookup_company(id)
    filing, financials = _latest_financials(company, period, amendments=amendments)
    superseded_by = _superseding_amendments(company, [filing])[filing.accession_no]
    return financials_response(
        company,
        filing,
        financials,
        period=period,
        view=view,
        dimensions=dimensions,
        amendments=amendments,
        superseded_by=superseded_by,
    )


@router.get("/company/{id}/financials/metrics")
def get_company_financial_metrics(
    id: str,
    period: FinancialsPeriod = "annual",
    amendments: bool = False,  # filing-selection policy: as-filed (false) vs restated (true)
) -> FinancialMetrics:
    company = lookup_company(id)
    filing, financials = _latest_financials(company, period, amendments=amendments)
    superseded_by = _superseding_amendments(company, [filing])[filing.accession_no]
    return metrics_response(
        company,
        filing,
        financials,
        period=period,
        amendments=amendments,
        superseded_by=superseded_by,
    )


@router.get("/company/{id}/financials/multi")
def get_company_financials_multi(
    id: str,
    period: FinancialsPeriod = "annual",
    n: Annotated[int, Query(ge=2, le=8)] = 4,  # filings stitched; each costs one SGML fetch
    view: FinancialsView = "standardized",
    dimensions: bool = False,
    amendments: bool = False,  # filing-selection policy: as-filed (false) vs restated (true)
) -> MultiFinancialsResponse:
    company = lookup_company(id)
    forms = _FORM_CHAIN[period]
    for form in forms:
        filings = list(company.get_filings(form=form, amendments=amendments, trigger_full_load=False).head(n))
        if filings:
            break
    else:
        raise HTTPException(
            status_code=404,
            detail=f"no {period} filing ({'/'.join(forms)}) at SEC for CIK {pad_cik(company.cik)}",
        )
    # selection above is the single amendment-policy gate; the stitcher must not re-filter
    xbrls = XBRLS.from_filings(filings, filter_amendments=False)
    standard = view == "standardized"
    stmt_view = StatementView.DETAILED if dimensions else StatementView.SUMMARY
    return multi_financials_response(
        company,
        filings,
        period=period,
        view=view,
        dimensions=dimensions,
        amendments=amendments,
        superseded_by=_superseding_amendments(company, filings),
        income_statement=xbrls.statements.income_statement(standard=standard, view=stmt_view),
        balance_sheet=xbrls.statements.balance_sheet(standard=standard, view=stmt_view),
        cashflow_statement=xbrls.statements.cashflow_statement(standard=standard, view=stmt_view),
        statement_of_equity=xbrls.statements.statement_of_equity(standard=standard, view=stmt_view),
        comprehensive_income=xbrls.statements.comprehensive_income(standard=standard, view=stmt_view),
    )


def _ttm_or_none(compute: Callable[[], TTMMetric]) -> TTMMetricModel | None:
    try:
        return ttm_metric_model(compute())
    except (KeyError, ValueError):  # concept absent or <4 consecutive quarters
        return None


@router.get("/company/{id}/financials/ttm")
def get_company_financials_ttm(
    id: str,
    concept: str | None = None,
    as_of: str | None = None,
) -> TTMResponse:
    company = lookup_company(id)
    if as_of is not None and _TTM_QUARTER_KEY.match(as_of) is None:
        try:  # the library accepts ISO dates or YYYY-QN quarter keys
            date.fromisoformat(as_of)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"as_of must be YYYY-MM-DD or YYYY-QN, got {as_of!r}") from None
    facts = company.get_facts()
    if facts is None:
        raise HTTPException(status_code=404, detail=f"no XBRL facts at SEC for CIK {pad_cik(company.cik)}")
    metric: TTMMetricModel | None = None
    if concept is not None:
        try:  # the explicitly requested concept fails loudly, unlike the convenience pair
            metric = ttm_metric_model(facts.get_ttm(concept, as_of))
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc).strip("'\"")) from None
    return TTMResponse(
        cik=pad_cik(company.cik),
        company=to_str(company.display_name),
        as_of=as_of,
        concept=concept,
        revenue=_ttm_or_none(lambda: facts.get_ttm_revenue(as_of)),
        net_income=_ttm_or_none(lambda: facts.get_ttm_net_income(as_of)),
        metric=metric,
    )
