"""Common wire models shared by every router (plan "Wire conventions")."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

CIK_PATTERN = r"^\d{10}$"
ACCESSION_PATTERN = r"^\d{10}-\d{2}-\d{6}$"


class WireModel(BaseModel):
    """Base for every response model: unknown constructor fields are converter bugs - fail loud."""

    model_config = ConfigDict(extra="forbid")


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
