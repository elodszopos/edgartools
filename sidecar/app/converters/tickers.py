"""SEC company-ticker-exchange DataFrame -> wire models, explicit field-by-field."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.cik import pad_cik
from app.models.tickers import TickerRef, TickersPage
from app.pagination import paginate
from app.serialize import to_str


def ticker_ref_from_row(row: dict[str, Any]) -> TickerRef:
    ticker = to_str(row["ticker"])
    if ticker is None:
        raise ValueError(f"ticker map row for cik {row['cik']!r} has no ticker symbol")
    return TickerRef(
        cik=pad_cik(row["cik"]),
        ticker=ticker,
        name=to_str(row["name"]),
        exchange=to_str(row["exchange"]),
    )


def tickers_page(data: pd.DataFrame, start: int, page_size: int) -> TickersPage:
    total = len(data)
    window = data.iloc[start : start + page_size]
    page = paginate(total, start, page_size)
    return TickersPage(
        tickers=[ticker_ref_from_row(row) for row in window.to_dict(orient="records")],
        total=total,
        start=start,
        page_size=page_size,
        has_more=page.has_more,
        next_start=page.next_start,
    )
