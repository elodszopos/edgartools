"""edgar `TwentyF` (Form 20-F) -> `TwentyFData`, explicit field-by-field.

Items are UNIQUE across the 20-F's five parts, so they reuse the shared catalog-lookup builder
(same mechanism as the 10-K -- the part is resolved from the static 20-F structure catalog).
Reading `obj.items` parses the primary HTML (bounded to this filing); `auditors`/`has_financials`
parse the filing's own XBRL. Heavyweight statement/note data stays out of the envelope (served by
the XBRL endpoints); only its presence is flagged.
"""

from __future__ import annotations

from typing import Any

from app.auditors import extract_auditors
from app.converters.forms.company_report import report_item_from_catalog
from app.models.forms.twentyf import TwentyFData
from app.serialize import to_date, to_iso_str, to_str


def twenty_f_data(obj: Any) -> TwentyFData:
    financials = obj.financials  # Financials | None (cached; reused by extract_auditors)
    form = to_str(obj.form) or ""
    auditors = extract_auditors(obj)
    return TwentyFData(
        form=form,
        is_amendment=form.endswith("/A"),
        report_period=to_date(obj.period_of_report),
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        items=[report_item_from_catalog(display, obj.structure) for display in obj.items],
        auditor=auditors[0] if auditors else None,
        auditors=auditors,
        has_financials=financials is not None,
        business=to_str(obj.business),
        risk_factors=to_str(obj.risk_factors),
        management_discussion=to_str(obj.management_discussion),
        operating_review=to_str(obj.operating_review),
        key_information=to_str(obj.key_information),
        major_shareholders=to_str(obj.major_shareholders),
        directors_and_employees=to_str(obj.directors_and_employees),
        company_information=to_str(obj.company_information),
        controls_and_procedures=to_str(obj.controls_and_procedures),
        financial_information=to_str(obj.financial_information),
    )
