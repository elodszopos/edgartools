"""Offset pagination shared by list endpoints (wire: start/page_size in, has_more/next_start out)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    """Where an offset window sits in the whole result set."""

    has_more: bool
    next_start: int | None


def paginate(total: int, start: int, page_size: int) -> Page:
    """Offset pagination over a known total: another page exists when this window leaves rows behind."""
    has_more = start + page_size < total
    return Page(has_more=has_more, next_start=start + page_size if has_more else None)
