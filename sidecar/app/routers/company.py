"""GET /company/{id} profile and GET /company/{id}/submissions filing history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.converters.company import company_profile, submissions_page
from app.deps import StartParam, lookup_company
from app.models.company import CompanyProfile, SubmissionsPage

router = APIRouter()


@router.get("/company/{id}")
def get_company(id: str) -> CompanyProfile:
    return company_profile(lookup_company(id))


@router.get("/company/{id}/submissions")
def get_company_submissions(
    id: str,
    form: str | None = None,
    start: StartParam = 0,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> SubmissionsPage:
    return submissions_page(lookup_company(id), form=form, start=start, page_size=page_size)
