"""edgar FinancialFact -> Fact wire model + list -> paged FactsResponse, field-by-field."""

from __future__ import annotations

from collections.abc import Sequence

from edgar.entity.core import Company
from edgar.entity.models import FinancialFact

from app.cik import pad_cik
from app.models.facts import Fact, FactsResponse
from app.pagination import paginate
from app.serialize import to_date, to_float, to_int, to_str


def fact_model(fact: FinancialFact) -> Fact:
    return Fact(
        concept=fact.concept,
        taxonomy=fact.taxonomy,
        label=fact.label,
        value=fact.value,
        numeric_value=to_float(fact.numeric_value),
        unit=fact.unit,
        scale=to_int(fact.scale),
        period_start=to_date(fact.period_start),
        period_end=to_date(fact.period_end),
        period_type=fact.period_type,
        fiscal_year=fact.fiscal_year,
        fiscal_period=to_str(fact.fiscal_period),
        filing_date=to_date(fact.filing_date),
        form_type=to_str(fact.form_type),
        accession=to_str(fact.accession),
        data_quality=fact.data_quality.value,
        is_audited=fact.is_audited,
        is_restated=fact.is_restated,
        is_estimated=fact.is_estimated,
        confidence_score=fact.confidence_score,
        semantic_tags=list(fact.semantic_tags),
        business_context=to_str(fact.business_context),
        calculation_context=to_str(fact.calculation_context),
        context_ref=to_str(fact.context_ref),
        dimensions=dict(fact.dimensions) if fact.dimensions else None,
        statement_type=to_str(fact.statement_type),
        line_item_sequence=to_int(fact.line_item_sequence),
        depth=to_int(fact.depth),
        parent_concept=to_str(fact.parent_concept),
        section=to_str(fact.section),
        is_abstract=fact.is_abstract,
        is_total=fact.is_total,
        presentation_order=to_float(fact.presentation_order),
        is_dimensioned=fact.is_dimensioned,
    )


def facts_page(
    company: Company,
    facts: Sequence[FinancialFact],
    *,
    start: int,
    page_size: int,
) -> FactsResponse:
    """Page an already-materialized fact list in memory (the facts store is in-memory)."""
    total = len(facts)
    page_info = paginate(total, start, page_size)
    window = facts[start : start + page_size]
    return FactsResponse(
        cik=pad_cik(company.cik),
        company=to_str(company.name),
        total=total,
        start=start,
        page_size=page_size,
        has_more=page_info.has_more,
        next_start=page_info.next_start,
        facts=[fact_model(fact) for fact in window],
    )
