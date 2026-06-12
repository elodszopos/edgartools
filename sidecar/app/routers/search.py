"""GET /search - EFTS full-text search (efts.sec.gov)."""

from __future__ import annotations

from datetime import date
from typing import Annotated

import orjson
from edgar.httprequests import get_with_retry
from edgar.reference.tickers import find_cik
from edgar.search.efts import EFTS_BASE_URL, build_efts_params, parse_aggregations, parse_hit
from fastapi import APIRouter, HTTPException, Query

from app.cik import pad_cik, parse_entity_id
from app.converters.search import EFTS_RESULT_WINDOW, search_page
from app.models.search import SearchPage

router = APIRouter()


def _build_efts_params(
    q: str,
    forms: list[str] | None,
    items: list[str] | None,
    cik: str | None,
    date_from: date | None,
    date_to: date | None,
    start: int,
) -> dict[str, str | int]:
    # delegate the wire encoding to the library's public builder (one source of truth);
    # the sidecar adds only its pagination offset on top. A unit test asserts equality.
    params: dict[str, str | int] = {
        **build_efts_params(
            q,
            forms=forms,
            items=items,
            cik=cik,
            start_date=date_from.isoformat() if date_from else None,
            end_date=date_to.isoformat() if date_to else None,
        )
    }
    if start > 0:
        params["from"] = start
    return params


@router.get("/search")
def search(
    q: str = "",
    forms: Annotated[list[str] | None, Query()] = None,
    items: Annotated[list[str] | None, Query()] = None,
    id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    start: Annotated[int, Query(ge=0)] = 0,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SearchPage:
    query = q.strip()
    if not query and not items:
        raise HTTPException(status_code=422, detail="provide a search query q, or an items filter (e.g. items=1.05)")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")
    if start + page_size > EFTS_RESULT_WINDOW:
        raise HTTPException(
            status_code=422,
            detail=f"start + page_size exceeds the EFTS result window of {EFTS_RESULT_WINDOW}; narrow the query instead",
        )

    cik: str | None = None
    if id is not None:
        entity = parse_entity_id(id)
        if isinstance(entity, int):
            cik = pad_cik(entity)
        else:
            resolved = find_cik(entity)
            if resolved is None:
                raise HTTPException(status_code=404, detail=f"ticker {entity!r} not found in the SEC ticker reference")
            cik = pad_cik(resolved)

    params = _build_efts_params(query, forms, items, cik, date_from, date_to, start)
    response = get_with_retry(EFTS_BASE_URL, params=params)
    data = orjson.loads(response.content)

    if "errorType" in data:
        # EFTS reports errors as HTTP 200 + error body; edgartools would render this as 0 hits
        message = str(data.get("errorMessage", ""))
        if "Result window" in message:
            raise HTTPException(status_code=422, detail=f"EFTS rejected the pagination window: {message}")
        raise HTTPException(status_code=502, detail=f"EFTS error: {message or data['errorType']}")

    hits = data.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    total_relation = hits.get("total", {}).get("relation", "eq")
    results = [parse_hit(hit) for hit in hits.get("hits", [])[:page_size]]
    aggregations = parse_aggregations(data.get("aggregations", {}))

    return search_page(
        query=query,
        results=results,
        total=total,
        total_relation=total_relation,
        aggregations=aggregations,
        start=start,
        page_size=page_size,
    )
