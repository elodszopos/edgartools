"""/filing/{accession} family: envelope, rendered content, detected sections, attachments."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field

from app.models.common import ACCESSION_PATTERN, CIK_PATTERN, Address, DocumentRef, WireModel
from app.models.forms.drs import DRSData
from app.models.forms.eightk import EightKData
from app.models.forms.form144 import Form144Data
from app.models.forms.formc import FormCData
from app.models.forms.formd import FormDData
from app.models.forms.fortyf import FortyFData
from app.models.forms.ncen import NcenData
from app.models.forms.ncsr import NcsrData
from app.models.forms.nmfp import NmfpData
from app.models.forms.nport import NPortData
from app.models.forms.ownership import OwnershipData
from app.models.forms.prospectus_424b import Prospectus424BData
from app.models.forms.prospectus_497k import Prospectus497KData
from app.models.forms.proxy import ProxyData
from app.models.forms.registration_s1 import RegistrationS1Data
from app.models.forms.registration_s3 import RegistrationS3Data
from app.models.forms.schedule13 import Schedule13DData, Schedule13GData
from app.models.forms.sixk import SixKData
from app.models.forms.tenk import TenKData
from app.models.forms.tenq import TenQData
from app.models.forms.thirteenf import Form13FData
from app.models.forms.twentyf import TwentyFData

ContentFormat = Literal["markdown", "text", "html"]
SectionFormat = Literal["text", "markdown"]
AttachmentFormat = Literal["text", "markdown", "raw"]


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
    business_address: Address | None
    mailing_address: Address | None
    former_names: list[FormerName]


class HeaderReportingOwner(WireModel):
    # raw conformed name as filed; resolving display order would need a per-owner SEC fetch
    name: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    company: CompanyInfo | None
    filing_values: FilingValues | None
    business_address: Address | None
    mailing_address: Address | None


class HeaderIssuer(WireModel):
    company: CompanyInfo | None
    business_address: Address | None
    mailing_address: Address | None
    former_names: list[FormerName]


class HeaderSubjectCompany(WireModel):
    company: CompanyInfo | None
    filing_values: FilingValues | None
    business_address: Address | None
    mailing_address: Address | None
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


# The typed-data union: one member per structurally-distinct filing.obj() payload, discriminated on
# `kind`. Canonical here; the converter imports this same alias so _typed_data's return type matches
# the envelope field exactly (one source of truth -- a new form adds its member in ONE place).
FilingData = (
    OwnershipData
    | EightKData
    | SixKData
    | Schedule13DData
    | Schedule13GData
    | Form13FData
    | TenKData
    | TenQData
    | TwentyFData
    | FortyFData
    | Form144Data
    | FormDData
    | FormCData
    | ProxyData
    | RegistrationS1Data
    | RegistrationS3Data
    | DRSData
    | Prospectus424BData
    | Prospectus497KData
    | NPortData
    | NmfpData
    | NcenData
    | NcsrData
)


class FilingEnvelope(WireModel):
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
    # obj_type (edgartools class name) is set ONLY when data is too - never advertised alone.
    # Discriminated on `kind`: ownership (3/4/5) | form8k | form6k | sc13d | sc13g | form13f |
    # form10k | form10q | form20f | form40f | form144 | formd | formc | proxy | registration_s1 |
    # registration_s3 | drs (drs wraps an S-1/S-3 payload as its own nested discriminated union) |
    # prospectus_424b (424B family; reuses the shared offering.py table legs) |
    # prospectus_497k (fund summary prospectus; HTML-parsed fund identity + share-class fees) |
    # nport (NPORT-P/EX fund portfolio report; lxml-parsed XML: header + general/fund info + holdings) |
    # nmfp (N-MFP2/N-MFP3 money market fund monthly report; general/series info + share classes + securities) |
    # ncen (N-CEN annual fund census; registrant + governance + per-series service providers/ETF mechanics) |
    # ncsr (N-CSR/N-CSRS certified shareholder report; Inline-XBRL oef: taxonomy -> per-fund funds[] (one per
    # SEC series) with fund-level figures + share-class expenses/returns; the one fund form built from
    # filing.xbrl(), not lxml).
    obj_type: str | None
    data: Annotated[FilingData, Field(discriminator="kind")] | None


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


class AttachmentInfo(WireModel):
    """One submission document; richer than the envelope's lean DocumentRef."""

    sequence: str
    document: str | None
    description: str | None
    # purpose-aware enhanced description (FilingSummary report name or standard exhibit text)
    display_description: str | None
    purpose: str | None
    document_type: str | None
    size: int | None
    ixbrl: bool
    extension: str | None
    # binary attachments have no JSON-safe content - fetch via url
    is_binary: bool
    is_primary: bool
    group: Literal["document", "data_file"]
    url: str | None


class AttachmentsResponse(WireModel):
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    total: int
    attachments: list[AttachmentInfo]


class AttachmentContentResponse(WireModel):
    accession_number: str = Field(pattern=ACCESSION_PATTERN)
    sequence: str
    document: str | None
    document_type: str | None
    fmt: AttachmentFormat
    # null when extraction yields nothing for the format (e.g. markdown of a non-HTML doc)
    content: str | None
