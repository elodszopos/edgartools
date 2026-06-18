"""Parse the SERIES-AND-CLASSES-CONTRACTS-DATA block from an N-CSR SGML header.

The open-end-fund Inline XBRL carries only an oef:ClassAxis (class C-ids), no series dimension, so a
multi-fund trust's facts cannot be grouped by series from the XBRL alone. The SGML header's SERIES
block is the authoritative registry: it groups classes under each SEC series and supplies the as-filed
series/class names and tickers. This is the public-API source for the per-series grouping (declaration
order preserved) onto which the ncsr converter attaches the oef XBRL figures keyed by class C-id.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# SGML is line-oriented: `<TAG>value` terminated by end-of-line; values carry no '<' or newline.
_SERIES_RE = re.compile(r"<SERIES>(.*?)</SERIES>", re.S)
_CLASS_RE = re.compile(r"<CLASS-CONTRACT>(.*?)</CLASS-CONTRACT>", re.S)


@dataclass(frozen=True)
class ClassContract:
    class_id: str | None
    class_name: str | None
    class_ticker: str | None


@dataclass(frozen=True)
class SeriesContract:
    series_id: str | None
    series_name: str | None
    classes: list[ClassContract]


def _tag(block: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>([^\r\n<]*)", block)
    if match is None:
        return None
    value = match.group(1).strip()
    return value or None


def parse_series_classes(header_text: str) -> list[SeriesContract]:
    """Return the trust's series in declaration order, each with its ordered class contracts."""
    series: list[SeriesContract] = []
    for series_match in _SERIES_RE.finditer(header_text):
        block = series_match.group(1)
        classes = [
            ClassContract(
                class_id=_tag(class_block, "CLASS-CONTRACT-ID"),
                class_name=_tag(class_block, "CLASS-CONTRACT-NAME"),
                class_ticker=_tag(class_block, "CLASS-CONTRACT-TICKER-SYMBOL"),
            )
            for class_block in (m.group(1) for m in _CLASS_RE.finditer(block))
        ]
        series.append(
            SeriesContract(
                series_id=_tag(block, "SERIES-ID"),
                series_name=_tag(block, "SERIES-NAME"),
                classes=classes,
            )
        )
    return series
