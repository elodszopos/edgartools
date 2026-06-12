"""Wire models for /search (EFTS full-text)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from app.models.common import ACCESSION_PATTERN, CIK_PATTERN, WireModel


class SearchResult(WireModel):
    # full fidelity vs edgartools EFTSResult: every parsed field crosses the wire
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    form: str
    filed: date
    company: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    period: date | None
    score: float
    file_type: str | None
    file_description: str | None
    document_id: str | None
    items: list[str]
    sic: str | None
    location: str | None
    state: str | None
    inc_state: str | None


class FacetBucket(WireModel):
    key: str
    count: int


class SearchAggregations(WireModel):
    entities: list[FacetBucket]
    sics: list[FacetBucket]
    states: list[FacetBucket]
    forms: list[FacetBucket]


class SearchPage(WireModel):
    query: str
    # EFTS caps reported totals at 10000: relation "gte" means "at least this many"
    total: int
    total_relation: Literal["eq", "gte"]
    results: list[SearchResult]
    aggregations: SearchAggregations
    start: int
    page_size: int
    has_more: bool
    next_start: int | None
