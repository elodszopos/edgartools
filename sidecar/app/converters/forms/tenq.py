"""edgar `TenQ` (Form 10-Q) -> `TenQData`, explicit field-by-field.

The edgar object is HTML/XBRL-backed and untyped, so the edgar side is `Any`. Reading `items`
parses the primary HTML; `auditors`/`has_financials` parse the filing's own XBRL -- both bounded to
this filing's artifacts. The heavyweight statement/note data stays out of the envelope (served by
the XBRL endpoints); only its presence is flagged.

Item parsing diverges from the 10-K: `TenQ.items` yields PART-QUALIFIED strings ("Part I, Item 1",
"Part II, Item 1A") because the same item number recurs across the two parts -- so the part comes
from the item string itself, and the title is a part-AWARE lookup (Part I Item 1 = "Financial
Statements" vs Part II Item 1 = "Legal Proceedings"). A bare "Item N" fallback (no part) is also
handled.
"""

from __future__ import annotations

import re
from typing import Any

from app.auditors import extract_auditors
from app.models.forms.company_report import ReportItem
from app.models.forms.tenq import TenQData
from app.serialize import to_date, to_iso_str, to_str

_PART_ITEM = re.compile(r"part\s+(i{1,2}|1|2)\s*,\s*item\s+(\d+[a-z]?)", re.IGNORECASE)  # "Part II, Item 1A"
_ITEM_ONLY = re.compile(r"item\s+(\d+[a-z]?)", re.IGNORECASE)  # bare "Item 1" fallback
_PART_ROMAN = {"1": "I", "2": "II", "I": "I", "II": "II"}


def _parse_item(display: str) -> tuple[str | None, str]:
    text = display.strip()
    part_item = _PART_ITEM.match(text)
    if part_item:
        return _PART_ROMAN.get(part_item.group(1).upper(), part_item.group(1).upper()), part_item.group(2).upper()
    item_only = _ITEM_ONLY.match(text)
    if item_only:
        return None, item_only.group(1).upper()
    return None, text  # unrecognized label -> keep raw so the item is never silently dropped


def _title(structure: Any, part: str | None, item_num: str) -> str | None:
    # part-aware: Part I Item 1 ("Financial Statements") != Part II Item 1 ("Legal Proceedings")
    item_key = f"ITEM {item_num}"
    entry = structure.get_item(item_key, f"PART {part}") if part else structure.get_item(item_key)
    return entry.get("Title") if isinstance(entry, dict) else None


def _item(display: str, structure: Any) -> ReportItem:
    part, item_num = _parse_item(display)
    return ReportItem(item=item_num, part=part, title=to_str(_title(structure, part, item_num)))


def ten_q_data(obj: Any) -> TenQData:
    financials = obj.financials  # Financials | None (cached; reused by extract_auditors)
    form = to_str(obj.form) or ""
    auditors = extract_auditors(obj)
    return TenQData(
        form=form,
        is_amendment=form.endswith("/A"),
        report_period=to_date(obj.period_of_report),
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        items=[_item(display, obj.structure) for display in obj.items],
        auditor=auditors[0] if auditors else None,
        auditors=auditors,
        has_financials=financials is not None,
    )
