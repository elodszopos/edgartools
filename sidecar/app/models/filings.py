"""Wire models for /filings and /filings/current."""

from __future__ import annotations

from datetime import datetime

from app.models.common import FilingRef, WireModel


class CurrentFilingRef(FilingRef):
    # getcurrent atom feed carries acceptance time; quarterly indexes do not
    accepted: datetime


class CurrentFilingsPage(WireModel):
    # the SEC feed exposes no total; has_more infers from raw (pre-filter) page fullness
    filings: list[CurrentFilingRef]
    start: int
    page_size: int
    has_more: bool
    next_start: int | None
