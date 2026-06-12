"""Shared FastAPI router dependencies: entity resolution glue + common query params."""

from __future__ import annotations

from typing import Annotated

from edgar.entity.core import Company
from fastapi import HTTPException, Query

from app.cik import parse_entity_id

# common offset cursor for every list endpoint; per-endpoint page_size bounds stay local
StartParam = Annotated[int, Query(ge=0)]


def lookup_company(id: str) -> Company:
    try:
        entity = parse_entity_id(id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    # unknown ticker raises CompanyNotFoundError (mapped to 404 in errors.py, with suggestions)
    company = Company(entity)
    if company.not_found:
        raise HTTPException(status_code=404, detail=f"no entity at SEC with CIK {company.cik}")
    return company
