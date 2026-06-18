"""/company/{id}/facts family: full-fidelity FinancialFact mirror + paged envelope.

Fact mirrors edgar.entity.models.FinancialFact field-for-field (same names) so the
parity gate is a direct attribute comparison and a new library field fails CI loudly.
Only the rendering helpers (to_llm_context / get_display_period_key / get_formatted_value
/ __repr__) are excluded; the is_dimensioned property is captured.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from app.models.common import CIK_PATTERN, WireModel


class Fact(WireModel):
    """One financial fact, every public surface of FinancialFact preserved."""

    # core identification
    concept: str
    taxonomy: str
    label: str

    # values (value is the raw reported value; numeric_value is the calc-ready float)
    value: float | int | str
    numeric_value: float | None
    unit: str
    scale: int | None

    # temporal context
    period_start: date | None
    period_end: date | None  # FinancialFact annotates `date` but assigns None when absent
    period_type: Literal["instant", "duration"]
    fiscal_year: int
    fiscal_period: str | None  # "FY"/"Q1".."Q4"; empty -> null

    # filing provenance (preserved per unit scope: form/filed/accn)
    filing_date: date | None
    form_type: str | None
    accession: str | None

    # quality and provenance
    data_quality: Literal["high", "medium", "low"]
    is_audited: bool
    is_restated: bool
    is_estimated: bool
    confidence_score: float

    # AI-ready context
    semantic_tags: list[str]
    business_context: str | None
    calculation_context: str | None

    # optional XBRL specifics
    context_ref: str | None
    dimensions: dict[str, str] | None
    statement_type: str | None
    line_item_sequence: int | None

    # structural metadata (from learned mappings)
    depth: int | None
    parent_concept: str | None
    section: str | None
    is_abstract: bool
    is_total: bool
    presentation_order: float | None

    # captured property (not a dataclass field): bool(dimensions)
    is_dimensioned: bool


class FactsResponse(WireModel):
    """Paged facts for one entity; shape mirrors SubmissionsPage (start/page_size in,
    has_more/next_start out). Used by /facts, /facts/concept/{c}, /facts/search alike."""

    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    total: int
    start: int
    page_size: int
    has_more: bool
    next_start: int | None
    facts: list[Fact]
