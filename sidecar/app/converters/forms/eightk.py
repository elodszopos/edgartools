"""edgar `CurrentReport` (Form 8-K, exported `EightK`) -> `EightKData`, explicit field-by-field.

The edgar object is pandas/HTML-backed and untyped, so the edgar side is `Any`. `items` yields
display strings ("Item 5.02"); each is normalized to its SEC number and titled from the static
`structure` catalog. Reading `has_earnings` parses the EX-99.1 earnings exhibit (bounded to this
filing) -- faithful to the object; the parsed tables themselves stay out of the envelope.
"""

from __future__ import annotations

import re
from typing import Any

from app.auditors import extract_auditors
from app.converters.common import document_ref
from app.models.forms.eightk import EightKData, EightKItem
from app.serialize import to_iso_str, to_str

# mirror edgar's private _normalize_item_number: "Item 2. 02" / "ITEM 2.02" -> "2.02"
_ITEM_PREFIX = re.compile(r"^item\s+", re.IGNORECASE)
_DOT_SPACES = re.compile(r"\s*\.\s*")


def _item_number(display: str) -> str:
    number = _ITEM_PREFIX.sub("", display.strip())
    number = _DOT_SPACES.sub(".", number)
    return number.rstrip(".")


def _item(display: str, structure: Any) -> EightKItem:
    # ItemOnlyFilingStructure.get_item upper-cases the key; a legacy single-digit item misses -> None
    entry = structure.get_item(display)
    title = entry.get("Title") if isinstance(entry, dict) else None
    return EightKItem(item=_item_number(display), title=to_str(title))


def eight_k_data(obj: Any) -> EightKData:
    auditors = extract_auditors(obj)
    return EightKData(
        form=to_str(obj.form) or "",
        is_amendment=bool(obj.is_amendment),
        company=to_str(obj.company),
        filing_date=to_iso_str(obj.filing_date),
        period_of_report=to_str(obj.period_of_report),
        content_type=obj.content_type,  # always a non-empty classification ("other" fallback)
        date_of_report=to_str(obj.date_of_report),  # "" (no period_of_report) -> null
        items=[_item(display, obj.structure) for display in obj.items],
        auditor=auditors[0] if auditors else None,
        has_press_release=bool(obj.has_press_release),
        has_earnings=bool(obj.has_earnings),
        balance_sheet=None,  # Statement object served at /xbrl, not inlined
        income_statement=None,  # Statement object served at /xbrl, not inlined
        cash_flow_statement=None,  # Statement object served at /xbrl, not inlined
        exhibits=[document_ref(att) for att in obj.get_exhibits()],
    )
