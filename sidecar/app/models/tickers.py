"""Wire models for /tickers (SEC company ticker map)."""

from __future__ import annotations

from pydantic import Field

from app.models.common import CIK_PATTERN, WireModel


class TickerRef(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    ticker: str
    name: str | None
    exchange: str | None  # null for OTC entries without an exchange listing


class TickersPage(WireModel):
    tickers: list[TickerRef]
    total: int
    start: int
    page_size: int
    has_more: bool
    next_start: int | None
