"""Typed `data` for Form 10-Q / 10-Q/A (the edgar `TenQ`).

A 10-Q is the quarterly twin of the 10-K but structurally distinct: its items span Part I
(Financial Information, Items 1-4) and Part II (Other Information, Items 1-6), so the SAME item
number (e.g. Item 1) appears in BOTH parts -- every item is therefore part-qualified. A 10-Q
carries no EX-21 subsidiary exhibit, so (unlike `TenKData`) there is no subsidiary list. The
`data` carries the structural item index, the auditor (present only when DEI auditor facts are
tagged -- 10-Q financials are unaudited, so usually absent), and a financials-presence flag.
Item/section TEXT ships via /content + /sections; the full statements via
/filing/{accession}/xbrl + /company/{id}/financials.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.common import WireModel
from app.models.forms.company_report import Auditor, ReportItem


class TenQData(WireModel):
    """filing.obj() for a 10-Q -- the edgar TenQ, lean structural fidelity."""

    kind: Literal["form10q"] = "form10q"
    form: str  # "10-Q" | "10-Q/A"
    is_amendment: bool
    report_period: date | None  # quarter-end the report covers (header period_of_report)
    company: str | None  # registrant name from the filing header
    filing_date: str | None  # ISO date string of when the filing was accepted
    items: list[ReportItem]  # detected part-qualified items; full text via /content + /sections
    auditor: Auditor | None  # first auditor; usually null (10-Q is unaudited)
    auditors: list[Auditor]  # usually empty (10-Q is unaudited); populated when DEI auditor facts are tagged
    has_financials: bool  # XBRL financials present -> /filing/{accession}/xbrl + /financials
