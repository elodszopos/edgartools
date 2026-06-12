"""GET /filing/{accession} - envelope from the quarterly-index lookup + SGML header."""

from __future__ import annotations

from typing import Annotated

from edgar._filings import get_by_accession_number_enriched
from fastapi import APIRouter, HTTPException, Path

from app.converters.filing import filing_envelope
from app.models.common import ACCESSION_PATTERN
from app.models.filing import FilingEnvelope

router = APIRouter()


@router.get("/filing/{accession}")
def get_filing(accession: Annotated[str, Path(pattern=ACCESSION_PATTERN)]) -> FilingEnvelope:
    # scans the accession year's quarterly indexes and collects every entity row;
    # current-year accessions missing from the indexes fall back to the getcurrent feed
    # (that fallback paginates the whole feed before concluding not-found - slow 404)
    filing = get_by_accession_number_enriched(accession)
    if filing is None:
        raise HTTPException(status_code=404, detail=f"no filing at SEC with accession {accession}")
    return filing_envelope(filing)
