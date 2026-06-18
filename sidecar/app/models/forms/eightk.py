"""Typed `data` for Form 8-K / 8-K/A (the edgar `CurrentReport`, exported as `EightK`).

A current report is item-structured: one or more numbered items (1.01-9.01) plus content
exhibits (press releases, agreements). The heavyweight EX-99.1 earnings-table parse
(`obj.earnings` / `income_statement` / ...) is OUT of the lean envelope -- `has_earnings`
flags its presence and the EX-99 exhibit is listed in `exhibits`; fetch the exhibit content
via /attachments/{seq}. Item and section TEXT ships via /content + /sections, not here.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import DocumentRef, WireModel
from app.models.forms.company_report import Auditor


class EightKItem(WireModel):
    item: str  # SEC item number, normalized from the object's display form ("Item 5.02" -> "5.02")
    title: str | None  # resolved from the static 8-K item catalog (CurrentReport.structure)


class EightKData(WireModel):
    """filing.obj() for an 8-K -- the edgar CurrentReport, full structural fidelity."""

    kind: Literal["form8k"] = "form8k"
    form: str  # "8-K" | "8-K/A"
    is_amendment: bool
    company: str | None  # registrant name from the filing header
    filing_date: str | None  # ISO date string of when the filing was accepted
    period_of_report: str | None  # header period_of_report (the event date from the header)
    content_type: str  # classification: earnings|director_change|material_agreement|asset_change|...
    date_of_report: str | None  # the event/report date, the object's own formatted string
    items: list[EightKItem]
    auditor: Auditor | None  # from earnings press release; null when no parseable earnings
    has_press_release: bool
    has_earnings: bool  # Item 2.02 present AND a parseable EX-99.1 earnings exhibit exists
    balance_sheet: str | None  # set to None -- Statement object served at /xbrl
    income_statement: str | None  # set to None -- Statement object served at /xbrl
    cash_flow_statement: str | None  # set to None -- Statement object served at /xbrl
    exhibits: list[DocumentRef]  # curated content exhibits (get_exhibits): EX-99, EX-10, ...
