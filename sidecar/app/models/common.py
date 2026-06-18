"""Common wire models shared by every router (plan "Wire conventions")."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

CIK_PATTERN = r"^\d{10}$"
ACCESSION_PATTERN = r"^\d{10}-\d{2}-\d{6}$"


class WireModel(BaseModel):
    """Base for every response model: unknown constructor fields are converter bugs - fail loud."""

    model_config = ConfigDict(extra="forbid")


class ErrorResponse(WireModel):
    """Canonical body for every non-2xx the sidecar emits (HTTPException, mapped
    edgartools/httpx exceptions, and flattened request-validation errors alike)."""

    detail: str


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI ``responses`` declaration: the given statuses carry an ErrorResponse body.

    Declaring 422 here also suppresses FastAPI's auto-added HTTPValidationError schema,
    which lies about the wire shape (the validation handler flattens detail to a string).
    """
    return {status: {"model": ErrorResponse} for status in statuses}


class Address(WireModel):
    """One address shape for every source. The submissions store carries the country
    description; the SGML header parse does not and serves it as null."""

    street1: str | None
    street2: str | None
    city: str | None
    state_or_country: str | None
    state_or_country_description: str | None
    zipcode: str | None


class EntityRef(WireModel):
    # nullable fields stay REQUIRED: absent -> null, keys never dropped (wire conventions)
    cik: str = Field(pattern=CIK_PATTERN)
    name: str | None


class FilingRef(WireModel):
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    form: str
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    filing_date: date


class FilingsPage(WireModel):
    filings: list[FilingRef]
    total: int | None
    start: int
    page_size: int
    has_more: bool
    next_start: int | None


class DocumentRef(WireModel):
    """A lean reference to one filing attachment (primary document or content exhibit).

    Shared by the envelope's primary_documents and the current-report forms' exhibits -
    one shape for "a submission document", content fetched separately via /attachments/{seq}."""

    sequence: str
    document: str | None
    description: str | None
    document_type: str | None
    size: int | None
    ixbrl: bool
    url: str | None
