"""GET /filing/{accession} family: envelope, rendered content, detected sections."""

from __future__ import annotations

from typing import Annotated

from edgar._filings import Filing, get_by_accession_number_enriched
from fastapi import APIRouter, HTTPException, Path

from app.converters.filing import (
    BinaryAttachmentError,
    attachment_content_response,
    attachments_response,
    content_response,
    filing_envelope,
    sections_response,
)
from app.converters.financials import filing_xbrl_response
from app.models.common import ACCESSION_PATTERN, error_responses
from app.models.filing import (
    AttachmentContentResponse,
    AttachmentFormat,
    AttachmentsResponse,
    ContentFormat,
    ContentResponse,
    FilingEnvelope,
    SectionFormat,
    SectionsResponse,
)
from app.models.financials import FilingXBRLResponse, FinancialsView

router = APIRouter(responses=error_responses(404, 422, 429, 502))

AccessionParam = Annotated[str, Path(pattern=ACCESSION_PATTERN)]
SequenceParam = Annotated[str, Path(pattern=r"^\d{1,4}$")]


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


@router.get("/filing/{accession}/xbrl")
def get_filing_xbrl(
    accession: AccessionParam,
    view: FinancialsView = "standardized",
    dimensions: bool = False,
) -> FilingXBRLResponse:
    # this filing's OWN XBRL statements (filing.xbrl()), not the company-level latest-10-K
    # selection /financials does; a filing with no XBRL (e.g. Form 4) -> 404, not empty
    filing = _lookup(accession)
    xbrl = filing.xbrl()
    if xbrl is None:
        raise HTTPException(status_code=404, detail=f"filing {accession} has no XBRL data")
    return filing_xbrl_response(filing, xbrl, view=view, dimensions=dimensions)


@router.get("/filing/{accession}/attachments")
def list_attachments(accession: AccessionParam) -> AttachmentsResponse:
    return attachments_response(_lookup(accession))


@router.get("/filing/{accession}/attachments/{sequence}")
def get_attachment_content(
    accession: AccessionParam,
    sequence: SequenceParam,
    fmt: AttachmentFormat = "text",
) -> AttachmentContentResponse:
    try:
        return attachment_content_response(_lookup(accession), sequence=sequence, fmt=fmt)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"no attachment with sequence {sequence} in {accession}") from error
    except BinaryAttachmentError as error:
        raise HTTPException(status_code=422, detail=f"binary attachment has no JSON content; fetch {error.url}") from error
