"""edgartools Filing -> wire models (envelope, content, sections), explicit field-by-field."""

from __future__ import annotations

import re
from datetime import date

from edgar._filings import Filing
from edgar._party import Address
from edgar.attachments import Attachment
from edgar.core import is_probably_html
from edgar.documents import HTMLParser, ParserConfig
from edgar.sgml.sgml_header import (
    CompanyInformation,
    Filer,
    FilingHeader,
    FilingInformation,
    FormerCompany,
    Issuer,
    ReportingOwner,
    SubjectCompany,
)

from app.cik import pad_cik
from app.models.filing import (
    CompanyInfo,
    ContentFormat,
    ContentResponse,
    DocumentRef,
    FilingEntity,
    FilingEnvelope,
    FilingHeaderModel,
    FilingValues,
    FormerName,
    HeaderAddress,
    HeaderFiler,
    HeaderIssuer,
    HeaderReportingOwner,
    HeaderSubjectCompany,
    SectionFormat,
    SectionInfo,
    SectionsResponse,
)
from app.serialize import eastern_naive_to_utc, to_date, to_int, to_str

# filing_metadata joins repeated ITEM INFORMATION values with ', ' (lossy) - parse the raw header text
_ITEM_LINE = re.compile(r"^ITEM INFORMATION:\s*(.+?)\s*$", re.MULTILINE)


def _address(address: Address | None) -> HeaderAddress | None:
    if address is None:
        return None
    return HeaderAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        zipcode=to_str(address.zipcode),
    )


def _company_info(info: CompanyInformation | None) -> CompanyInfo | None:
    if info is None:
        return None
    cik = to_str(info.cik)
    return CompanyInfo(
        name=to_str(info.name),
        cik=pad_cik(cik) if cik else None,
        sic=to_str(info.sic),
        irs_number=to_str(info.irs_number),
        state_of_incorporation=to_str(info.state_of_incorporation),
        fiscal_year_end=to_str(info.fiscal_year_end),
    )


def _filing_values(values: FilingInformation | None) -> FilingValues | None:
    if values is None:
        return None
    return FilingValues(
        form=to_str(values.form),
        file_number=to_str(values.file_number),
        sec_act=to_str(values.sec_act),
        film_number=to_str(values.film_number),
    )


def _former_names(names: list[FormerCompany] | None) -> list[FormerName]:
    return [FormerName(name=to_str(n.name), date_of_change=to_date(n.date_of_change)) for n in names or []]


def _filer(filer: Filer) -> HeaderFiler:
    return HeaderFiler(
        company=_company_info(filer.company_information),
        filing_values=_filing_values(filer.filing_information),
        business_address=_address(filer.business_address),
        mailing_address=_address(filer.mailing_address),
        former_names=_former_names(filer.former_company_names),
    )


def _reporting_owner(owner: ReportingOwner) -> HeaderReportingOwner:
    # Owner.name lazily fetches the entity from SEC to fix name order - serve the raw
    # conformed name from the header artifact instead (no cross-entity calls in envelopes)
    raw_name = owner.owner._raw_name if owner.owner else None  # noqa: SLF001
    raw_cik = to_str(owner.owner.cik) if owner.owner else None
    return HeaderReportingOwner(
        name=to_str(raw_name),
        cik=pad_cik(raw_cik) if raw_cik else None,
        company=_company_info(owner.company_information),
        filing_values=_filing_values(owner.filing_information),
        business_address=_address(owner.business_address),
        mailing_address=_address(owner.mailing_address),
    )


def _issuer(issuer: Issuer | None) -> HeaderIssuer | None:
    if issuer is None:
        return None
    return HeaderIssuer(
        # Issuer.former_company_names exists on the dataclass but the header parse never fills it
        company=_company_info(issuer.company_information),
        business_address=_address(issuer.business_address),
        mailing_address=_address(issuer.mailing_address),
    )


def _subject_company(subject: SubjectCompany) -> HeaderSubjectCompany:
    return HeaderSubjectCompany(
        company=_company_info(subject.company_information),
        filing_values=_filing_values(subject.filing_information),
        business_address=_address(subject.business_address),
        mailing_address=_address(subject.mailing_address),
        former_names=_former_names(subject.former_company_names),
    )


def header_model(header: FilingHeader) -> FilingHeaderModel:
    return FilingHeaderModel(
        acceptance_datetime=eastern_naive_to_utc(header.acceptance_datetime),
        filing_date=to_date(header.filing_date),
        period_of_report=to_date(header.period_of_report),
        date_as_of_change=to_date(header.date_as_of_change),
        document_count=to_int(header.document_count),
        items=_ITEM_LINE.findall(header.text),
        filers=[_filer(f) for f in header.filers or []],
        # the parser appends None for empty REPORTING-OWNER blocks
        reporting_owners=[_reporting_owner(ro) for ro in header.reporting_owners or [] if ro is not None],
        issuer=_issuer(header.issuer),
        subject_companies=[_subject_company(sc) for sc in header.subject_companies or []],
    )


def _document_ref(attachment: Attachment) -> DocumentRef:
    return DocumentRef(
        sequence=attachment.sequence_number,
        document=to_str(attachment.document),
        description=to_str(attachment.description),
        document_type=to_str(attachment.document_type),
        size=to_int(attachment.size),
        ixbrl=bool(attachment.ixbrl),
        url=attachment.url if not attachment.empty else None,
    )


def _entities(filing: Filing, primary_date: date) -> list[FilingEntity]:
    # all_entities: first row is the primary {cik, company}; index-sourced related rows
    # also carry form/filing_date - normalize missing keys to the primary filing's values
    entities = []
    for row in filing.all_entities:
        row_date = to_date(row.get("filing_date"))
        entities.append(
            FilingEntity(
                cik=pad_cik(row["cik"]),
                company=to_str(row["company"]),
                form=row.get("form", filing.form),
                filing_date=row_date if row_date is not None else primary_date,
            )
        )
    return entities


def content_response(filing: Filing, fmt: ContentFormat, page_breaks: bool) -> ContentResponse:
    if fmt == "html":
        content = filing.html()
    elif fmt == "text":
        content = filing.text()
    else:
        content = filing.markdown(include_page_breaks=page_breaks)
    return ContentResponse(accession_number=filing.accession_no, fmt=fmt, content=content)


def sections_response(filing: Filing, fmt: SectionFormat) -> SectionsResponse:
    # modern parser (Filing.sections() still rides the deprecated edgar.files chunker);
    # forms without section structure (e.g. rendered Form 4 XML) yield an empty list
    html = filing.html()
    sections: list[SectionInfo] = []
    if html and is_probably_html(html):
        document = HTMLParser(ParserConfig(form=filing.form)).parse(html)
        ordered = sorted(document.sections.items(), key=lambda kv: (kv[1].start_offset, kv[0]))
        for name, section in ordered:
            sections.append(
                SectionInfo(
                    name=name,
                    title=section.title,
                    part=section.part,
                    item=section.item,
                    detection_method=section.detection_method,
                    confidence=float(section.confidence),
                    content=section.text() if fmt == "text" else section.markdown(),
                )
            )
    return SectionsResponse(accession_number=filing.accession_no, fmt=fmt, total=len(sections), sections=sections)


def filing_envelope(filing: Filing) -> FilingEnvelope:
    sgml = filing.sgml()
    filing_date = to_date(filing.filing_date)
    if filing_date is None:
        # every index row and feed entry carries a filing date; absence means the lookup broke
        raise ValueError(f"filing {filing.accession_no} has no filing date")
    return FilingEnvelope(
        accession_number=filing.accession_no,
        form=filing.form,
        cik=pad_cik(filing.cik),
        company=to_str(filing.company),
        filing_date=filing_date,
        is_multi_entity=filing.is_multi_entity,
        entities=_entities(filing, filing_date),
        header=header_model(sgml.header),
        primary_documents=[_document_ref(a) for a in sgml.attachments.primary_documents],
        homepage_url=filing.homepage_url,
        text_url=filing.text_url,
        obj_type=filing.obj_type,
        data=None,
    )
