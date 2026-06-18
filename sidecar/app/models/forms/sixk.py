"""Typed `data` for Form 6-K / 6-K/A (the edgar `SixK`, Report of Foreign Private Issuer).

6-K has NO numbered item structure -- its payload is cover-page metadata (commission file
number, report month, the 20-F/40-F annual-report checkbox, a free-text description of the
material contained) plus content exhibits. XBRL financials (rare, IFRS taxonomy) are served by
the XBRL/financials endpoints, not duplicated here. Exhibit content ships via /attachments/{seq}.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import DocumentRef, WireModel


class SixKData(WireModel):
    """filing.obj() for a 6-K -- the edgar SixK, full fidelity (cover metadata + exhibits)."""

    kind: Literal["form6k"] = "form6k"
    form: str  # "6-K" | "6-K/A"
    company: str | None  # registrant name from the filing header
    filing_date: str | None  # ISO date string of when the filing was accepted
    date_of_report: str | None  # the event/report date, the object's own formatted string
    commission_file_number: str | None  # cover-page "Commission File Number" (e.g. "001-14948")
    report_month: str | None  # cover-page "For the month of ..." (e.g. "March 2026")
    annual_report_form: str | None  # the checked annual-report form: "20-F" | "40-F" | None
    content_description: str | None  # cover-page "Material Contained in this Report" text
    has_exhibits: bool
    has_press_release: bool
    exhibits: list[DocumentRef]  # non-graphic content exhibits (excludes the cover page itself)
