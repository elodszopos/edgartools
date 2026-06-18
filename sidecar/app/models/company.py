"""/company/{id} family: profile from the SEC submissions store + paged filing history."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from app.models.common import ACCESSION_PATTERN, CIK_PATTERN, Address, WireModel


class EntityFormerName(WireModel):
    name: str | None
    from_date: date | None
    to_date: date | None


class CompanyProfile(WireModel):
    """Everything the SEC submissions JSON says about the entity - no cross-filing fetches."""

    cik: str = Field(pattern=CIK_PATTERN)
    name: str | None
    # individuals are conformed "Last First Middle"; display_name restores natural order
    display_name: str | None
    entity_type: str | None
    tickers: list[str]
    # parallel to tickers; entries can be null for unlisted classes
    exchanges: list[str | None]
    sic: str | None
    sic_description: str | None
    # raw SEC category string; filer_status + qualifier flags are its parsed form
    category: str | None
    filer_status: str | None
    is_smaller_reporting_company: bool
    is_emerging_growth_company: bool
    fiscal_year_end: str | None
    ein: str | None
    phone: str | None
    description: str | None
    website: str | None
    investor_website: str | None
    state_of_incorporation: str | None
    state_of_incorporation_description: str | None
    # null when no incorporation code is on file (resolving it would need cross-filing analysis)
    is_foreign: bool | None
    flags: str | None
    business_address: Address | None
    mailing_address: Address | None
    former_names: list[EntityFormerName]
    insider_transaction_for_owner_exists: bool
    insider_transaction_for_issuer_exists: bool
    is_company: bool
    is_individual: bool
    is_bdc: bool


class SubmissionFiling(WireModel):
    """One row of the entity's filing history (richer than quarterly-index rows)."""

    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    form: str
    filing_date: date
    report_date: date | None
    acceptance_datetime: datetime | None
    act: str | None
    file_number: str | None
    # SEC item codes (e.g. "2.02"), not the header's item descriptions
    items: list[str]
    size: int | None
    is_xbrl: bool | None
    is_inline_xbrl: bool | None
    primary_document: str | None
    primary_doc_description: str | None


class SubmissionsPage(WireModel):
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    total: int
    start: int
    page_size: int
    has_more: bool
    next_start: int | None
    filings: list[SubmissionFiling]
