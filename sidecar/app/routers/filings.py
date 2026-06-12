"""GET /filings (quarterly indexes) and GET /filings/current (getcurrent feed)."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, cast

import pyarrow as pa
from edgar import get_filings
from edgar._filings import Filings
from edgar.core import IntString
from edgar.current_filings import get_current_entries_on_page
from fastapi import APIRouter, HTTPException, Query

from app.cik import parse_entity_id
from app.converters.filings import current_filings_page, filings_page
from app.models.common import FilingsPage
from app.models.filings import CurrentFilingsPage

router = APIRouter()


@router.get("/filings")
def list_filings(
    year: Annotated[int | None, Query(ge=1994, le=2100)] = None,
    quarter: Annotated[int | None, Query(ge=1, le=4)] = None,
    form: Annotated[list[str] | None, Query()] = None,
    amendments: bool = True,
    date_from: date | None = None,
    date_to: date | None = None,
    id: str | None = None,
    start: Annotated[int, Query(ge=0)] = 0,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> FilingsPage:
    if (date_from or date_to) and (year or quarter):
        raise HTTPException(status_code=422, detail="use either year/quarter or date_from/date_to, not both")
    if (date_from is None) != (date_to is None):
        # open-ended ranges would expand to every quarterly index since 1994 - keep requests bounded
        raise HTTPException(status_code=422, detail="date_from and date_to must be provided together")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")

    filing_date = f"{date_from.isoformat()}:{date_to.isoformat()}" if date_from and date_to else None
    # cast: List[IntString] is invariant, list[str] is a safe member
    forms = cast("list[IntString] | None", form)
    filings = get_filings(year=year, quarter=quarter, form=forms, amendments=amendments, filing_date=filing_date)
    if filings is None:
        raise HTTPException(status_code=422, detail="no SEC index for the requested period")

    if id is not None:
        entity = parse_entity_id(id)
        filings = filings.filter(cik=entity) if isinstance(entity, int) else filings.filter(ticker=entity)

    return filings_page(filings, start=start, page_size=page_size)


@router.get("/filings/current")
def list_current_filings(
    form: str = "",
    owner: Literal["include", "exclude", "only"] = "include",
    amendments: bool = True,
    start: Annotated[int, Query(ge=0)] = 0,
    page_size: int = 40,
) -> CurrentFilingsPage:
    if page_size not in (10, 20, 40, 80, 100):
        # the getcurrent feed only serves these page sizes; anything else would be silently clamped
        raise HTTPException(status_code=422, detail="page_size must be one of 10, 20, 40, 80, 100")
    entries = get_current_entries_on_page(count=page_size, start=start, form=form, owner=owner)
    if not entries:
        return CurrentFilingsPage(filings=[], start=start, page_size=page_size, has_more=False, next_start=None)
    filings = Filings(pa.Table.from_pylist(entries))
    if form:
        # SEC's getcurrent ignores its type param (edgartools issue #501) - filter client-side
        filings = filings.filter(form=form, amendments=amendments)
    return current_filings_page(filings, raw_count=len(entries), start=start, page_size=page_size)
