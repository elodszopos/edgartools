"""GET /company/{id} profile and GET /company/{id}/submissions filing history."""

from __future__ import annotations

from typing import Annotated

from edgar.entity.core import Company
from fastapi import APIRouter, HTTPException, Query

from app.cik import parse_entity_id
from app.converters.company import company_profile, submissions_page
from app.models.company import CompanyProfile, SubmissionsPage

router = APIRouter()


def _lookup(id: str) -> Company:
    try:
        entity = parse_entity_id(id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    # unknown ticker raises CompanyNotFoundError (mapped to 404 in errors.py, with suggestions)
    company = Company(entity)
    if company.not_found:
        raise HTTPException(status_code=404, detail=f"no entity at SEC with CIK {company.cik}")
    return company


@router.get("/company/{id}")
def get_company(id: str) -> CompanyProfile:
    return company_profile(_lookup(id))


@router.get("/company/{id}/submissions")
def get_company_submissions(
    id: str,
    form: str | None = None,
    start: Annotated[int, Query(ge=0)] = 0,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> SubmissionsPage:
    return submissions_page(_lookup(id), form=form, start=start, page_size=page_size)
