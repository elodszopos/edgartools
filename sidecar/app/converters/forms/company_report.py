"""Converters shared across the edgar `CompanyReport` family (10-K / 10-Q / 20-F / 40-F).

The static item-structure catalog is inherited from the edgar `CompanyReport` base, so two
item-building strategies recur:

  - catalog lookup (10-K, 20-F): `obj.items` are UNIQUE "Item N" strings, so the part is found by
    scanning the form's static structure catalog -> `report_item_from_catalog`.
  - part-qualified (10-Q): `obj.items` are "Part X, Item Y" (the same number recurs across parts),
    so the part comes from the string and the title is a part-aware lookup -> stays in the 10-Q
    converter.

Multi-auditor extraction (shared across the family too) lives in `app.auditors`.
"""

from __future__ import annotations

import re
from typing import Any

from app.models.forms.company_report import ReportItem
from app.serialize import to_str

_ITEM_PREFIX = re.compile(r"^item\s+", re.IGNORECASE)  # "Item 1A" -> "1A"


def _part_for_item(structure: Any, display: str) -> str | None:
    # structure.structure is {"PART I": {"ITEM 1": {...}}, ...}; find the Part owning this item
    key = display.strip().upper()
    for part_name, items in structure.structure.items():
        if key in items:
            return part_name.upper().removeprefix("PART ").strip() or None
    return None


def report_item_from_catalog(display: str, structure: Any) -> ReportItem:
    """ReportItem for forms whose items are UNIQUE across parts (10-K, 20-F): the part is looked up
    from the form's static structure catalog and the title from get_item (which scans all parts).
    The 10-Q must NOT use this (its item numbers collide across parts)."""
    entry = structure.get_item(display)  # upper-cases the key internally; {Title, Description}|None
    title = entry.get("Title") if isinstance(entry, dict) else None
    return ReportItem(item=_ITEM_PREFIX.sub("", display.strip()), part=_part_for_item(structure, display), title=to_str(title))
