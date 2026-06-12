"""GET /company/{id}/financials (statements) and /financials/metrics (scalars)."""

from __future__ import annotations

from edgar._filings import Filing
from edgar.entity.core import Company
from edgar.financials import Financials
from fastapi import APIRouter, HTTPException

from app.cik import pad_cik
from app.converters.financials import financials_response, metrics_response
from app.models.financials import FinancialMetrics, FinancialsPeriod, FinancialsResponse, FinancialsView
from app.routers.company import _lookup

router = APIRouter()

# mirrors Company.get_financials / get_quarterly_financials fallback chains; the filing
# is selected here (not via those methods) so the response can carry its provenance
_FORM_CHAIN: dict[str, tuple[str, ...]] = {
    "annual": ("10-K", "20-F", "40-F"),
    "quarterly": ("10-Q", "6-K"),
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
    company = _lookup(id)
    filing, financials = _latest_financials(company, period)
    return financials_response(company, filing, financials, period=period, view=view, dimensions=dimensions)


@router.get("/company/{id}/financials/metrics")
def get_company_financial_metrics(
    id: str,
    period: FinancialsPeriod = "annual",
) -> FinancialMetrics:
    company = _lookup(id)
    filing, financials = _latest_financials(company, period)
    return metrics_response(company, filing, financials, period=period)
