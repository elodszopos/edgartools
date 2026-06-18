"""edgar `SixK` (Form 6-K) -> `SixKData`, explicit field-by-field.

The cover-page fields (commission_file_number, report_month, annual_report_form,
content_description) are regex-parsed by edgar from the primary document's text; absent ->
null. `exhibits` is edgar's curated non-graphic attachment list (cover page excluded).
"""

from __future__ import annotations

from typing import Any

from app.converters.common import document_ref
from app.models.forms.sixk import SixKData
from app.serialize import to_iso_str, to_str


def six_k_data(obj: Any) -> SixKData:
    return SixKData(
        form=to_str(obj.form) or "",
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        date_of_report=to_str(obj.date_of_report),  # "" (no period_of_report) -> null
        commission_file_number=to_str(obj.commission_file_number),
        report_month=to_str(obj.report_month),
        annual_report_form=to_str(obj.annual_report_form),
        content_description=to_str(obj.content_description),
        has_exhibits=bool(obj.has_exhibits),
        has_press_release=bool(obj.has_press_release),
        exhibits=[document_ref(att) for att in obj.exhibits],
    )
