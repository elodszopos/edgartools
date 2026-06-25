"""edgar `TenK` (Form 10-K) -> `TenKData`, explicit field-by-field.

The edgar object is HTML/XBRL-backed and untyped, so the edgar side is `Any`. Reading `items`
parses the primary HTML; `auditors`/`has_financials` parse the filing's own XBRL -- both bounded to
this filing's artifacts, faithful to the object. The heavyweight statement/note data itself stays
out of the envelope (served by the XBRL endpoints); only its presence is flagged.
"""

from __future__ import annotations

from typing import Any

from app.auditors import extract_auditors
from app.converters.forms.company_report import report_item_from_catalog
from app.models.forms.tenk import Subsidiary, TenKData
from app.serialize import to_date, to_float, to_iso_str, to_str


def _subsidiary(sub: Any) -> Subsidiary:
    return Subsidiary(
        name=to_str(sub.name) or "",
        jurisdiction=to_str(sub.jurisdiction) or "",
        ownership_pct=to_float(sub.ownership_pct),
    )


def ten_k_data(obj: Any) -> TenKData:
    subsidiaries = obj.subsidiaries  # SubsidiaryList | None (None == no EX-21 exhibit)
    financials = obj.financials  # Financials | None (cached; reused by extract_auditors)
    form = to_str(obj.form) or ""
    auditors = extract_auditors(obj)
    return TenKData(
        form=form,
        is_amendment=form.endswith("/A"),
        report_period=to_date(obj.period_of_report),
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        items=[report_item_from_catalog(display, obj.structure) for display in obj.items],
        auditor=auditors[0] if auditors else None,
        auditors=auditors,
        has_subsidiaries=subsidiaries is not None,
        subsidiaries=[_subsidiary(s) for s in subsidiaries] if subsidiaries is not None else [],
        has_financials=financials is not None,
        business=to_str(obj.business),
        risk_factors=to_str(obj.risk_factors),
        management_discussion=to_str(obj.management_discussion),
        directors_officers_and_governance=to_str(obj.directors_officers_and_governance),
    )
