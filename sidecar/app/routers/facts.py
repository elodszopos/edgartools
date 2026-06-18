"""GET /company/{id}/facts (+ /facts/concept/{concept}, /facts/search) — entity XBRL facts.

Backed by EntityFacts: /facts pages get_all_facts(); /facts/concept/{c} runs
query().by_concept (fuzzy on concept OR label, exact=true for an indexed exact match);
/facts/search runs query().by_text (case-insensitive regex across the text fields).
"""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from app.cik import pad_cik
from app.converters.facts import facts_page
from app.deps import PageSizeParam, StartParam, lookup_company
from app.models.common import error_responses
from app.models.facts import FactsResponse

router = APIRouter(responses=error_responses(404, 422, 429, 502))


def _entity_facts(id: str):
    """Resolve the entity and its facts store; 404 when SEC has no XBRL facts for it."""
    company = lookup_company(id)
    facts = company.get_facts()
    if facts is None:
        raise HTTPException(status_code=404, detail=f"no XBRL facts at SEC for CIK {pad_cik(company.cik)}")
    return company, facts


@router.get("/company/{id}/facts")
def get_company_facts(
    id: str,
    start: StartParam = 0,
    page_size: PageSizeParam = 100,
) -> FactsResponse:
    company, facts = _entity_facts(id)
    return facts_page(company, facts.get_all_facts(), start=start, page_size=page_size)


@router.get("/company/{id}/facts/concept/{concept}")
def get_company_facts_concept(
    id: str,
    concept: str,
    exact: bool = False,  # false: fuzzy substring on concept OR label; true: indexed exact concept
    start: StartParam = 0,
    page_size: PageSizeParam = 100,
) -> FactsResponse:
    company, facts = _entity_facts(id)
    matched = facts.query().by_concept(concept, exact=exact).execute()
    return facts_page(company, matched, start=start, page_size=page_size)


@router.get("/company/{id}/facts/search")
def search_company_facts(
    id: str,
    q: str,
    start: StartParam = 0,
    page_size: PageSizeParam = 100,
) -> FactsResponse:
    company, facts = _entity_facts(id)
    try:  # by_text compiles q as a regex eagerly; a bad pattern is a client error, not a 500
        matched = facts.query().by_text(q).execute()
    except re.error as exc:
        raise HTTPException(status_code=422, detail=f"invalid search regex {q!r}: {exc}") from exc
    return facts_page(company, matched, start=start, page_size=page_size)
