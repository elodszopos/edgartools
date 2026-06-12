"""GET /filing/{accession} family: envelope, rendered content, detected sections."""

from __future__ import annotations

from typing import Annotated

from edgar._filings import Filing, get_by_accession_number_enriched
from fastapi import APIRouter, HTTPException, Path

from app.converters.filing import content_response, filing_envelope, sections_response
from app.models.common import ACCESSION_PATTERN
from app.models.filing import ContentFormat, ContentResponse, FilingEnvelope, SectionFormat, SectionsResponse

router = APIRouter()

AccessionParam = Annotated[str, Path(pattern=ACCESSION_PATTERN)]


def _lookup(accession: str) -> Filing:
    # scans the accession year's quarterly indexes and collects every entity row;
    # current-year accessions missing from the indexes fall back to the getcurrent feed
    # (that fallback paginates the whole feed before concluding not-found - slow 404)
    filing = get_by_accession_number_enriched(accession)
    if filing is None:
        raise HTTPException(status_code=404, detail=f"no filing at SEC with accession {accession}")
    return filing


@router.get("/filing/{accession}")
def get_filing(accession: AccessionParam) -> FilingEnvelope:
    return filing_envelope(_lookup(accession))


@router.get("/filing/{accession}/content")
def get_filing_content(
    accession: AccessionParam,
    fmt: ContentFormat = "markdown",
    page_breaks: bool = False,
) -> ContentResponse:
    if page_breaks and fmt != "markdown":
        raise HTTPException(status_code=422, detail="page_breaks only applies to fmt=markdown")
    return content_response(_lookup(accession), fmt=fmt, page_breaks=page_breaks)


@router.get("/filing/{accession}/sections")
def get_filing_sections(accession: AccessionParam, fmt: SectionFormat = "text") -> SectionsResponse:
    return sections_response(_lookup(accession), fmt=fmt)
