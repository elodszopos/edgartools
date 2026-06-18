"""Shared FastAPI router dependencies: entity resolution glue + common query params."""

from __future__ import annotations

from typing import Annotated

from edgar.entity.core import Company
from edgar.reference.tickers import find_cik
from fastapi import HTTPException, Query

from app.cik import pad_cik, parse_entity_id

# common offset cursor for every list endpoint
StartParam = Annotated[int, Query(ge=0)]

# common page size for index-backed list endpoints; endpoints whose source dictates
# other bounds (tickers dump, EFTS window, getcurrent fixed sizes) declare their own
PageSizeParam = Annotated[int, Query(ge=1, le=1000)]


def resolve_entity_id(id: str) -> int | str:
    """Wire `id` param: digits -> CIK int, anything else -> ticker string; malformed -> 422."""
    try:
        return parse_entity_id(id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def resolve_cik(id: str) -> int:
    """Like resolve_entity_id, but tickers resolve through the SEC ticker reference -> 404
    when unknown. For endpoints that filter by CIK without loading the entity."""
    entity = resolve_entity_id(id)
    if isinstance(entity, int):
        return entity
    cik = find_cik(entity)
    if cik is None:
        raise HTTPException(status_code=404, detail=f"ticker {entity!r} not found in the SEC ticker reference")
    return int(cik)


def lookup_company(id: str) -> Company:
    # unknown ticker raises CompanyNotFoundError (mapped to 404 in errors.py, with suggestions)
    company = Company(resolve_entity_id(id))
    if company.not_found:
        raise HTTPException(status_code=404, detail=f"no entity at SEC with CIK {pad_cik(company.cik)}")
    return company
