"""Typed `data` for Form 10-K / 10-K/A (the edgar `TenK`).

Pass-through: edgar exposes X, sidecar exposes X.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.common import WireModel
from app.models.forms.company_report import Auditor, ReportItem


class Subsidiary(WireModel):
    name: str
    jurisdiction: str
    ownership_pct: float | None


class TenKData(WireModel):
    kind: Literal["form10k"] = "form10k"
    form: str
    is_amendment: bool
    report_period: date | None
    company: str | None
    filing_date: str | None
    items: list[ReportItem]
    auditor: Auditor | None  # first (current-period) auditor; null when no DEI auditor facts
    auditors: list[Auditor]
    has_subsidiaries: bool
    subsidiaries: list[Subsidiary]
    has_financials: bool
    business: str | None
    risk_factors: str | None
    management_discussion: str | None
    directors_officers_and_governance: str | None
