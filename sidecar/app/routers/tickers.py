"""GET /tickers - the SEC company ticker map (cik, ticker, name, exchange)."""

from __future__ import annotations

from typing import Annotated

from edgar.reference.tickers import get_company_ticker_name_exchange
from fastapi import APIRouter, Query

from app.converters.tickers import tickers_page
from app.deps import StartParam
from app.models.tickers import TickersPage

router = APIRouter()


@router.get("/tickers")
def list_tickers(
    start: StartParam = 0,
    # defaults serve the whole ~10k-row map in one request; paging exists for uniformity
    page_size: Annotated[int, Query(ge=1, le=20_000)] = 20_000,
) -> TickersPage:
    data = get_company_ticker_name_exchange()
    return tickers_page(data, start=start, page_size=page_size)
