"""Nested wire models shared across the edgar `CompanyReport` family (10-K / 10-Q / 20-F / 40-F).

These forms inherit the same `auditors` (XBRL DEI facts) and the same item-index shape from the
edgar `CompanyReport` base, so the wire models live here once -- one OpenAPI component, one Zod
type -- rather than being duplicated per form. Form-specific nested models (e.g. the 10-K-only
EX-21 `Subsidiary`) stay in their own form module.
"""

from __future__ import annotations

from app.models.common import WireModel


class ReportItem(WireModel):
    """One detected item in a periodic report's structural index (text served by /content + /sections)."""

    item: str  # canonical SEC item number, normalized from "Item 1A" -> "1A"
    part: str | None  # owning Part roman numeral ("I"/"II"/.. ) -- a 10-Q item is part-qualified, a 10-K item is unique
    title: str | None  # SEC standard item title from the form's static structure catalog


class Auditor(WireModel):
    """One audit firm from the XBRL DEI facts. A filing carries several when it reports an
    auditor change -- current + prior, each tagged on its own period context."""

    name: str
    location: str | None  # city/country; edgar '' (DEI fact absent) normalizes to null
    firm_id: int | None  # PCAOB firm ID; null when the DEI fact is absent
    icfr_attestation: bool  # auditor attested to internal control over financial reporting
    period_end: str | None  # fiscal period end this auditor signed for (distinguishes current vs prior)
