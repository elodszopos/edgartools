"""edgar `FortyF` (Form 40-F) -> `FortyFData`, explicit field-by-field.

Maps the wrapper's own bounded artifacts plus AIF section text: `form` + `period_of_report`
(header), `auditors`/`has_financials` (the 40-F wrapper's own iXBRL), and named AIF sections
(`obj.items`, `obj.business`, `obj[name]`) whose first access downloads the AIF exhibit (cached).
Raw-format properties (`aif_html`, `aif_text`, `mda_html`, `mda_text`, `mda_attachment`) are
excluded from the wire -- they're source content, not parsed structured data.
"""

from __future__ import annotations

from typing import Any

from app.auditors import extract_auditors
from app.models.forms.fortyf import FortyFData
from app.serialize import to_date, to_iso_str, to_str


def _section(obj: Any, name: str) -> str | None:
    try:
        val = obj[name]
        return to_str(val) if val else None
    except (KeyError, TypeError, AttributeError, IndexError):
        return None


def forty_f_data(obj: Any) -> FortyFData:
    financials = obj.financials  # the 40-F wrapper's own iXBRL (cached; reused by extract_auditors)
    form = to_str(obj.form) or ""
    auditors = extract_auditors(obj)
    return FortyFData(
        form=form,
        is_amendment=form.endswith("/A"),
        report_period=to_date(obj.period_of_report),
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        items=obj.items or [],
        business=to_str(obj.business) if obj.business else None,
        risk_factors=_section(obj, "Risk Factors"),
        corporate_structure=_section(obj, "Corporate Structure"),
        capital_structure=_section(obj, "Description Of Capital Structure"),
        dividends=_section(obj, "Dividends"),
        directors_and_officers=_section(obj, "Directors And Officers"),
        legal_proceedings=_section(obj, "Legal Proceedings"),
        auditor=auditors[0] if auditors else None,
        auditors=auditors,
        has_financials=financials is not None,
    )
