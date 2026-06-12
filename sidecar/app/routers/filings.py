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

from app.converters.filings import current_filings_page, filings_page
from app.deps import PageSizeParam, StartParam, resolve_cik
from app.models.common import FilingsPage, error_responses
from app.models.filings import CurrentFilingsPage, CurrentPageSize

router = APIRouter(responses=error_responses(422, 429, 502))


@router.get("/filings", responses=error_responses(404))
def list_filings(
    year: Annotated[int | None, Query(ge=1994, le=2100)] = None,
    quarter: Annotated[int | None, Query(ge=1, le=4)] = None,
    form: Annotated[list[str] | None, Query()] = None,
    amendments: bool = True,
    date_from: date | None = None,
    date_to: date | None = None,
    id: str | None = None,
    start: StartParam = 0,
    page_size: PageSizeParam = 50,
) -> FilingsPage:
    if (date_from or date_to) and (year or quarter):
        raise HTTPException(status_code=422, detail="use either year/quarter or date_from/date_to, not both")
    if (date_from is None) != (date_to is None):
        # open-ended ranges would expand to every quarterly index since 1994 - keep requests bounded
        raise HTTPException(status_code=422, detail="date_from and date_to must be provided together")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")

    # tickers resolve up front (unknown -> 404, like /company and /search) and BEFORE the
    # index download; filter(ticker=...) would silently yield an empty page instead
    cik = resolve_cik(id) if id is not None else None

    filing_date = f"{date_from.isoformat()}:{date_to.isoformat()}" if date_from and date_to else None
    # cast: List[IntString] is invariant, list[str] is a safe member
    forms = cast("list[IntString] | None", form)
    filings = get_filings(year=year, quarter=quarter, form=forms, amendments=amendments, filing_date=filing_date)
    if filings is None:
        raise HTTPException(status_code=422, detail="no SEC index for the requested period")

    if cik is not None:
        filings = filings.filter(cik=cik)

    return filings_page(filings, start=start, page_size=page_size)


@router.get("/filings/current")
def list_current_filings(
    form: str = "",
    owner: Literal["include", "exclude", "only"] = "include",
    amendments: bool = True,
    start: StartParam = 0,
    page_size: CurrentPageSize = CurrentPageSize.FORTY,
) -> CurrentFilingsPage:
    entries = get_current_entries_on_page(count=int(page_size), start=start, form=form, owner=owner)
    if not entries:
        return CurrentFilingsPage(filings=[], start=start, page_size=page_size, has_more=False, next_start=None)
    filings = Filings(pa.Table.from_pylist(entries))
    if form:
        # SEC's getcurrent ignores its type param (edgartools issue #501) - filter client-side
        filings = filings.filter(form=form, amendments=amendments)
    elif not amendments:
        # the amendments param must hold without a form filter too; short pages follow the
        # same documented raw-count paging contract as the form filter above
        filings = filings.filter(amendments=False)
    return current_filings_page(filings, raw_count=len(entries), start=start, page_size=page_size)
