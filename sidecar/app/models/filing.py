"""/filing/{accession} family: envelope, rendered content, and detected sections."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.models.common import ACCESSION_PATTERN, CIK_PATTERN, WireModel

ContentFormat = Literal["markdown", "text", "html"]
SectionFormat = Literal["text", "markdown"]


class HeaderAddress(WireModel):
    # state_or_country_description excluded: the SGML header parse never populates it
    street1: str | None
    street2: str | None
    city: str | None
    state_or_country: str | None
    zipcode: str | None


class CompanyInfo(WireModel):
    name: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    sic: str | None
    irs_number: str | None
    state_of_incorporation: str | None
    fiscal_year_end: str | None


class FilingValues(WireModel):
    form: str | None
    file_number: str | None
    sec_act: str | None
    film_number: str | None


class FormerName(WireModel):
    name: str | None
    date_of_change: date | None


class HeaderFiler(WireModel):
    company: CompanyInfo | None
    filing_values: FilingValues | None
    business_address: HeaderAddress | None
    mailing_address: HeaderAddress | None
    former_names: list[FormerName]


class HeaderReportingOwner(WireModel):
    # raw conformed name as filed; resolving display order would need a per-owner SEC fetch
    name: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    company: CompanyInfo | None
    filing_values: FilingValues | None
    business_address: HeaderAddress | None
    mailing_address: HeaderAddress | None


class HeaderIssuer(WireModel):
    company: CompanyInfo | None
    business_address: HeaderAddress | None
    mailing_address: HeaderAddress | None


class HeaderSubjectCompany(WireModel):
    company: CompanyInfo | None
    filing_values: FilingValues | None
    business_address: HeaderAddress | None
    mailing_address: HeaderAddress | None
    former_names: list[FormerName]


class FilingHeaderModel(WireModel):
    acceptance_datetime: datetime | None
    filing_date: date | None
    period_of_report: date | None
    date_as_of_change: date | None
    document_count: int | None
    items: list[str]
    filers: list[HeaderFiler]
    reporting_owners: list[HeaderReportingOwner]
    issuer: HeaderIssuer | None
    subject_companies: list[HeaderSubjectCompany]


class FilingEntity(WireModel):
    """One quarterly-index row for the accession (primary entity first)."""

    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    form: str
    filing_date: date


class DocumentRef(WireModel):
    sequence: str
    document: str | None
    description: str | None
    document_type: str | None
    size: int | None
    ixbrl: bool
    url: str | None


class FilingEnvelope(WireModel):
    # `data` becomes the typed-form discriminated union when the first P4 unit (U40) lands
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    form: str
    cik: str = Field(pattern=CIK_PATTERN)
    company: str | None
    filing_date: date
    is_multi_entity: bool
    entities: list[FilingEntity]
    header: FilingHeaderModel
    primary_documents: list[DocumentRef]
    homepage_url: str
    text_url: str
    obj_type: str | None
    data: None


class ContentResponse(WireModel):
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    fmt: ContentFormat
    # null when the filing has no renderable document for the format (e.g. scanned paper)
    content: str | None


class SectionInfo(WireModel):
    name: str
    title: str
    part: str | None
    item: str | None
    detection_method: str
    confidence: float
    content: str


class SectionsResponse(WireModel):
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    fmt: SectionFormat
    total: int
    sections: list[SectionInfo]
