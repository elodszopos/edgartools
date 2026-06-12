"""EFTS hit dicts -> wire models, explicit field-by-field.

Hit/aggregation parsing stays in edgartools (edgar.search.efts) - the fork's parsers are
the single source of truth; this module only maps their output onto wire models.
"""

from __future__ import annotations

from typing import Literal

from edgar.search.efts import EFTSAggregations, EFTSResult

from app.cik import pad_cik
from app.models.search import FacetBucket, SearchAggregations, SearchPage, SearchResult
from app.serialize import to_date

# empirical (D2, 2026-06-12): EFTS rejects from+size > 10000 ("Result window is too large")
EFTS_RESULT_WINDOW = 10_000


def search_result_from_efts(result: EFTSResult) -> SearchResult:
    filed = to_date(result.filed)
    if filed is None:
        # every EFTS hit carries file_date; absence means the upstream parser broke
        raise ValueError(f"EFTS hit {result.accession_number} has no file_date")
    return SearchResult(
        accession_number=result.accession_number,
        form=result.form,
        filed=filed,
        company=result.company,
        cik=pad_cik(result.cik) if result.cik else None,
        period=to_date(result.period),
        score=result.score,
        file_type=result.file_type,
        file_description=result.file_description,
        document_id=result.document_id,
        items=result.items,
        sic=result.sic,
        location=result.location,
        state=result.state,
        inc_state=result.inc_state,
    )


def search_aggregations_from_efts(aggregations: EFTSAggregations | None) -> SearchAggregations:
    if aggregations is None:
        return SearchAggregations(entities=[], sics=[], states=[], forms=[])
    return SearchAggregations(
        entities=[FacetBucket(key=a.key, count=a.count) for a in aggregations.entities],
        sics=[FacetBucket(key=a.key, count=a.count) for a in aggregations.sics],
        states=[FacetBucket(key=a.key, count=a.count) for a in aggregations.states],
        forms=[FacetBucket(key=a.key, count=a.count) for a in aggregations.forms],
    )


def search_page(
    query: str,
    results: list[EFTSResult],
    total: int,
    total_relation: Literal["eq", "gte"],
    aggregations: EFTSAggregations | None,
    start: int,
    page_size: int,
) -> SearchPage:
    # pagination can never pass the EFTS window, however large the reported total
    reachable = min(total, EFTS_RESULT_WINDOW)
    has_more = start + page_size < reachable
    return SearchPage(
        query=query,
        total=total,
        total_relation=total_relation,
        results=[search_result_from_efts(result) for result in results],
        aggregations=search_aggregations_from_efts(aggregations),
        start=start,
        page_size=page_size,
        has_more=has_more,
        next_start=start + page_size if has_more else None,
    )
