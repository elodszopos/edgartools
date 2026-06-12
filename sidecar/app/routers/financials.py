"""GET /company/{id}/financials (+ /metrics, /multi stitched, /ttm trailing-twelve-months)."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from typing import TYPE_CHECKING, Annotated

from edgar._filings import Filing
from edgar.entity.core import ANNUAL_FINANCIAL_FORMS, QUARTERLY_FINANCIAL_FORMS, Company
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
from app.models.financials import (
    FinancialMetrics,
    FinancialsPeriod,
    FinancialsResponse,
    FinancialsView,
    MultiFinancialsResponse,
    TTMMetricModel,
    TTMResponse,
)
from app.serialize import to_str

if TYPE_CHECKING:
    from edgar.ttm.calculator import TTMMetric

router = APIRouter()

_TTM_QUARTER_KEY = re.compile(r"^\d{4}-[Qq][1-4]$")

# the period -> form fallback chain, sourced from edgartools' public constants so the
# sidecar and Company.get_financials / get_quarterly_financials cannot drift apart; the
# filing is selected here (not via those methods) so the response can carry its provenance
_FORM_CHAIN: dict[str, tuple[str, ...]] = {
    "annual": ANNUAL_FINANCIAL_FORMS,
    "quarterly": QUARTERLY_FINANCIAL_FORMS,
}


def _latest_financials(company: Company, period: FinancialsPeriod) -> tuple[Filing, Financials]:
    forms = _FORM_CHAIN[period]
    for form in forms:
        filing = company.get_filings(form=form, amendments=False, trigger_full_load=False).latest()
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


@router.get("/company/{id}/financials")
def get_company_financials(
    id: str,
    period: FinancialsPeriod = "annual",
    view: FinancialsView = "standardized",
    dimensions: bool = False,
) -> FinancialsResponse:
    company = lookup_company(id)
    filing, financials = _latest_financials(company, period)
    return financials_response(company, filing, financials, period=period, view=view, dimensions=dimensions)


@router.get("/company/{id}/financials/metrics")
def get_company_financial_metrics(
    id: str,
    period: FinancialsPeriod = "annual",
) -> FinancialMetrics:
    company = lookup_company(id)
    filing, financials = _latest_financials(company, period)
    return metrics_response(company, filing, financials, period=period)


@router.get("/company/{id}/financials/multi")
def get_company_financials_multi(
    id: str,
    period: FinancialsPeriod = "annual",
    n: Annotated[int, Query(ge=2, le=8)] = 4,  # filings stitched; each costs one SGML fetch
    view: FinancialsView = "standardized",
    dimensions: bool = False,
) -> MultiFinancialsResponse:
    company = lookup_company(id)
    forms = _FORM_CHAIN[period]
    for form in forms:
        filings = list(company.get_filings(form=form, amendments=False, trigger_full_load=False).head(n))
        if filings:
            break
    else:
        raise HTTPException(
            status_code=404,
            detail=f"no {period} filing ({'/'.join(forms)}) at SEC for CIK {pad_cik(company.cik)}",
        )
    xbrls = XBRLS.from_filings(filings)
    standard = view == "standardized"
    stmt_view = StatementView.DETAILED if dimensions else StatementView.SUMMARY
    return multi_financials_response(
        company,
        filings,
        period=period,
        view=view,
        dimensions=dimensions,
        income_statement=xbrls.statements.income_statement(standard=standard, view=stmt_view),
        balance_sheet=xbrls.statements.balance_sheet(standard=standard, view=stmt_view),
        cashflow_statement=xbrls.statements.cashflow_statement(standard=standard, view=stmt_view),
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
