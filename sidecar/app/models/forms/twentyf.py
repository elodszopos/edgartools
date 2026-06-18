"""Typed `data` for Form 20-F / 20-F/A (the edgar `TwentyF`).

The 20-F is the annual report for foreign private issuers (IFRS or US-GAAP filers, ADRs). It is
item-structured like the 10-K -- Items 1-19 across Parts I-V, each item UNIQUE across the parts --
so its items reuse the catalog-lookup builder (part resolved from the static 20-F structure),
unlike the 10-Q's part-qualified items. There is no EX-21 subsidiary list (a domestic-filer
exhibit). The `data` carries the structural item index, the signing auditor (XBRL DEI facts), and
a financials-presence flag. Item/section TEXT ships via /content + /sections; full statements via
/filing/{accession}/xbrl + /company/{id}/financials.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.common import WireModel
from app.models.forms.company_report import Auditor, ReportItem


class TwentyFData(WireModel):
    """filing.obj() for a 20-F -- the edgar TwentyF, lean structural fidelity."""

    kind: Literal["form20f"] = "form20f"
    form: str  # "20-F" | "20-F/A"
    is_amendment: bool
    report_period: date | None  # fiscal year-end the report covers (header period_of_report)
    company: str | None  # registrant name from the filing header
    filing_date: str | None  # ISO date string of when the filing was accepted
    items: list[ReportItem]  # detected items (unique across parts, catalog-titled); text via /content + /sections
    auditor: Auditor | None  # first (current-period) auditor; null when no DEI auditor facts
    auditors: list[Auditor]  # all disclosed auditors, current period first; empty when no XBRL DEI auditor facts
    has_financials: bool  # XBRL financials present -> /filing/{accession}/xbrl + /financials
    business: str | None  # Item 4 text (Information on the Company)
    risk_factors: str | None  # Item 3 text (Key Information / risk factors)
    management_discussion: str | None  # Item 5 text (Operating and Financial Review)
    operating_review: str | None  # Item 5 text (alias for management_discussion)
    key_information: str | None  # Item 3 text
    major_shareholders: str | None  # Item 7 text
    directors_and_employees: str | None  # Item 6 text
    company_information: str | None  # Item 4 text (alias for business)
    controls_and_procedures: str | None  # Item 15 text
    financial_information: str | None  # Item 8 text
