"""Typed `data` for Form 40-F / 40-F/A (the edgar `FortyF`).

The 40-F is the Canadian MJDS annual report: a thin SEC wrapper around the Canadian Annual
Information Form (AIF) and MD&A, filed as EX-1/EX-99 exhibits. The AIF is downloaded once
(one SEC request); all NI 51-102 section headings and parsed section text are extracted from
that single download. Raw HTML/text blobs and MD&A live at /content + /attachments.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.common import WireModel
from app.models.forms.company_report import Auditor


class FortyFData(WireModel):
    """filing.obj() for a 40-F -- the edgar FortyF."""

    kind: Literal["form40f"] = "form40f"
    form: str  # "40-F" | "40-F/A"
    is_amendment: bool
    report_period: date | None  # fiscal year-end the report covers (header period_of_report)
    company: str | None  # registrant name from the filing header
    filing_date: str | None  # ISO date string of when the filing was accepted
    items: list[str]  # detected NI 51-102 AIF section headings
    business: str | None  # "Description of the Business" AIF section text
    risk_factors: str | None  # "Risk Factors" AIF section text
    corporate_structure: str | None  # "Corporate Structure" AIF section text
    capital_structure: str | None  # "Description of Capital Structure" AIF section text
    dividends: str | None  # "Dividends" AIF section text
    directors_and_officers: str | None  # "Directors and Officers" AIF section text
    legal_proceedings: str | None  # "Legal Proceedings" AIF section text
    auditor: Auditor | None  # first auditor from the 40-F wrapper's iXBRL DEI facts; null when untagged
    auditors: list[Auditor]  # from the 40-F wrapper's own iXBRL DEI facts; empty when untagged
    has_financials: bool  # the 40-F wrapper carries iXBRL financials -> /filing/{accession}/xbrl
