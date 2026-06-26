"""edgartools Filing -> wire models (envelope, content, sections), explicit field-by-field."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date

from edgar import matches_form
from edgar._filings import Filing
from edgar._party import Address
from edgar.attachments import Attachment
from edgar.core import is_probably_html
from edgar.documents import HTMLParser, ParserConfig
from edgar.funds.ncen import NCEN_FORMS
from edgar.funds.ncsr import NCSR_FORMS
from edgar.funds.nmfp3 import MONEY_MARKET_FORMS
from edgar.funds.reports import NPORT_FORMS
from edgar.proxy import PROXY_FORMS
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
from edgar.thirteenf import THIRTEENF_FORMS
from httpx import HTTPError

from app.cik import pad_cik
from app.converters.common import document_ref
from app.converters.forms.drs import drs_data
from app.converters.forms.eightk import eight_k_data
from app.converters.forms.form144 import form_144_data
from app.converters.forms.effect import effect_data
from app.converters.forms.formc import form_c_data
from app.converters.forms.formd import form_d_data
from app.converters.forms.fortyf import forty_f_data
from app.converters.forms.ncen import ncen_data
from app.converters.forms.ncsr import ncsr_data
from app.converters.forms.nmfp import nmfp_data
from app.converters.forms.npx import npx_data
from app.converters.forms.nport import nport_data
from app.converters.forms.ownership import ownership_data
from app.converters.forms.prospectus_424b import prospectus_424b_data
from app.converters.forms.prospectus_497k import prospectus_497k_data
from app.converters.forms.proxy import proxy_data
from app.converters.forms.registration_s1 import registration_s1_data
from app.converters.forms.registration_s3 import registration_s3_data
from app.converters.forms.schedule13 import schedule_13d_data, schedule_13g_data
from app.converters.forms.sixk import six_k_data
from app.converters.forms.tenk import ten_k_data
from app.converters.forms.tenq import ten_q_data
from app.converters.forms.thirteenf import form_13f_data
from app.converters.forms.twentyf import twenty_f_data
from app.models.common import Address as WireAddress
from app.models.filing import (
    AttachmentContentResponse,
    AttachmentFormat,
    AttachmentInfo,
    AttachmentsResponse,
    CompanyInfo,
    ContentFormat,
    ContentResponse,
    FilingData,
    FilingEntity,
    FilingEnvelope,
    FilingHeaderModel,
    FilingValues,
    FormerName,
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


def _address(address: Address | None) -> WireAddress | None:
    if address is None:
        return None
    return WireAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        # the SGML header parse never populates the description; null per the canonical shape
        state_or_country_description=None,
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
    raw_name = owner.owner.raw_name if owner.owner else None
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
        company=_company_info(issuer.company_information),
        business_address=_address(issuer.business_address),
        mailing_address=_address(issuer.mailing_address),
        former_names=_former_names(issuer.former_company_names),
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


class BinaryAttachmentError(Exception):
    """Raised when raw content is requested for an attachment that decodes to bytes."""

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.url = url


def _attachment_info(attachment: Attachment, *, is_primary: bool, group: str) -> AttachmentInfo:
    return AttachmentInfo(
        sequence=attachment.sequence_number,
        document=to_str(attachment.document),
        description=to_str(attachment.description),
        display_description=to_str(attachment.display_description),
        purpose=to_str(attachment.purpose),
        document_type=to_str(attachment.document_type),
        size=to_int(attachment.size),
        ixbrl=bool(attachment.ixbrl),
        extension=to_str(attachment.extension),
        is_binary=attachment.is_binary(),
        is_primary=is_primary,
        group="document" if group == "document" else "data_file",
        url=attachment.url if not attachment.empty else None,
    )


def attachments_response(filing: Filing) -> AttachmentsResponse:
    # sgml-sourced attachments: documents first, then data files (the SGML build latches
    # everything after the first XML data file into data_files); primary = sequence-1 docs.
    # membership by sequence_number, not object identity - the library may rebuild
    # Attachment objects between the documents and primary_documents accessors
    attachments = filing.attachments
    primary_sequences = {p.sequence_number for p in attachments.primary_documents}
    rows = [_attachment_info(a, is_primary=a.sequence_number in primary_sequences, group="document") for a in attachments.documents]
    rows += [_attachment_info(a, is_primary=a.sequence_number in primary_sequences, group="data_file") for a in attachments.data_files or []]
    return AttachmentsResponse(accession_number=filing.accession_no, total=len(rows), attachments=rows)


def attachment_content_response(filing: Filing, sequence: str, fmt: AttachmentFormat) -> AttachmentContentResponse:
    # raises KeyError when the sequence is absent (router maps to 404)
    attachment = filing.attachments.get_by_sequence(sequence)
    content: str | None
    if fmt == "raw":
        if attachment.is_binary():
            raise BinaryAttachmentError(attachment.url)
        raw = attachment.content
        content = raw if isinstance(raw, str) else None
    elif fmt == "text":
        # untyped upstream: binary docs yield None, everything else extracts to str
        text = attachment.text()
        content = text if isinstance(text, str) else None
    else:
        content = attachment.markdown()
    return AttachmentContentResponse(
        accession_number=filing.accession_no,
        sequence=attachment.sequence_number,
        document=to_str(attachment.document),
        document_type=to_str(attachment.document_type),
        fmt=fmt,
        content=content,
    )


# P4 typed `data`: one (forms, builder) row per form unit. obj() is gated to these forms so an
# unsupported-form envelope never pays obj()'s xbrl()-fallthrough parse (edgar.obj falls to
# filing.xbrl() for unmapped forms) - keeps those envelopes lean. Forms 3/4/5 share OwnershipData.
# builders take the obj; form_d_data also needs the raw offering XML (its co-issuers / related-person
# roles live only there), so the row signature is the looser Callable[..., FilingData]
_DATA_BUILDERS: list[tuple[list[str], Callable[..., FilingData]]] = [
    (["4"], ownership_data),  # U40 (ownership; Forms 3/4/5 share OwnershipData)
    (["3"], ownership_data),  # U41
    (["5"], ownership_data),  # U42
    (["8-K"], eight_k_data),  # U43 (current report; matches_form handles the "8-K/A" suffix)
    (["6-K"], six_k_data),  # U43 (foreign private issuer report; matches_form handles "6-K/A")
    # U44 beneficial ownership: both string variants (modern "SCHEDULE 13D" + legacy "SC 13D"),
    # matches_form expands each to its "/A" amendment - exactly Schedule13D.from_filing's accept set
    (["SCHEDULE 13D", "SC 13D"], schedule_13d_data),  # U44
    (["SCHEDULE 13G", "SC 13G"], schedule_13g_data),  # U44
    # U45 13F family: edgar's own accept set (13F-HR/NT/CTR + /A); one ThirteenF -> Form13FData
    (THIRTEENF_FORMS, form_13f_data),  # U45
    (["10-K"], ten_k_data),  # U46 (annual report; matches_form handles the "10-K/A" suffix)
    (["10-Q"], ten_q_data),  # U47 (quarterly report; matches_form handles the "10-Q/A" suffix)
    (["20-F"], twenty_f_data),  # U48 (foreign-issuer annual report; matches_form handles "20-F/A")
    (["40-F"], forty_f_data),  # U48 (Canadian MJDS annual report; matches_form handles "40-F/A")
    (["144"], form_144_data),  # U49 (Rule 144 proposed-sale notice; matches_form handles "144/A")
    (["D"], form_d_data),  # U50 (Reg D exempt-offering notice; matches_form handles "D/A")
    # U51 Reg Crowdfunding: edgar's own obj() accept set; one FormC backs every variant -> FormCData
    (["C", "C-U", "C-AR", "C-TR"], form_c_data),  # matches_form expands each to its "/A" amendment
    # U52 proxy family: edgar's own PROXY_FORMS accept set (DEF 14A + every 14A variant incl. /A) ->
    # one ProxyStatement -> ProxyData; the specific form is the `form` field
    (PROXY_FORMS, proxy_data),  # U52a
    # U53a S-1/F-1 registration: edgar obj() maps both (+/A) to one RegistrationS1; matches_form
    # expands each to its "/A" amendment - exactly edgar's ['S-1','F-1'] obj() accept set
    (["S-1", "F-1"], registration_s1_data),  # U53a
    # U54 S-3/F-3 shelf registration: edgar obj() maps the whole shelf family (+/A) to one
    # RegistrationS3; this is exactly edgar's ['S-3','S-3ASR','S-3D','S-3DPOS','F-3','F-3ASR'] accept
    # set, matches_form expanding each base form to its "/A" amendment
    (["S-3", "S-3ASR", "S-3D", "S-3DPOS", "F-3", "F-3ASR"], registration_s3_data),  # U54
    # U53b DRS draft registration: edgar maps DRS (+/A) to DraftRegistrationStatement, which detects
    # the underlying form and embeds a RegistrationS1/RegistrationS3 payload (U53a/U54) where one
    # exists; matches_form("DRS") expands to the "DRS/A" amendment - edgar's exact obj() accept set
    (["DRS"], drs_data),  # U53b
    # U55a 424B prospectus family: edgar obj() maps every 424B variant (+/A) to one Prospectus424B;
    # this is exactly edgar's ['424B1','424B2','424B3','424B4','424B5','424B7','424B8'] accept set
    # (no 424B6, no 424A), matches_form expanding each to its "/A" amendment
    (["424B1", "424B2", "424B3", "424B4", "424B5", "424B7", "424B8"], prospectus_424b_data),  # U55a
    # U55b 497K fund summary prospectus: edgar obj() maps 497K (+/A) to one Prospectus497K; ZERO XBRL
    # (HTML-table parsed). matches_form("497K") expands to the "497K/A" amendment - edgar's exact set
    (["497K"], prospectus_497k_data),  # U55b
    # U56 NPORT-P/NPORT-EX fund portfolio report: edgar obj() maps the whole family to one FundReport;
    # NPORT_FORMS is edgar's exact accept set ["NPORT-P","NPORT-EX","N-PORT","N-PORT/A"]. ZERO XBRL
    # (lxml-parsed XML). matches_form expands each base form to its "/A" amendment.
    (NPORT_FORMS, nport_data),  # U56
    # U57a N-MFP2/N-MFP3 money market fund monthly report: edgar obj() maps MONEY_MARKET_FORMS to one
    # MoneyMarketFund; that constant is edgar's exact accept set (N-MFP2/N-MFP3 + each "/A"). ZERO XBRL
    # (lxml-parsed XML; both schema versions feed one MoneyMarketFund).
    (MONEY_MARKET_FORMS, nmfp_data),  # U57a
    # U57b N-CEN annual fund census: edgar obj() maps NCEN_FORMS to one FundCensus; that constant is
    # edgar's exact accept set (["N-CEN","N-CEN/A"]). ZERO XBRL (lxml-parsed XML).
    (NCEN_FORMS, ncen_data),  # U57b
    # U57c N-CSR/N-CSRS certified shareholder report: edgar obj() maps NCSR_FORMS to one
    # FundShareholderReport; that constant is edgar's exact accept set (N-CSR/N-CSRS + each "/A"). The
    # ONLY fund form built from filing.xbrl() (Inline XBRL, oef: taxonomy) -- gating to these forms
    # BEFORE obj() keeps the (legitimate) xbrl() parse scoped to N-CSR; a non-open-end filer with no
    # oef XBRL -> from_filing returns None -> data=null.
    (NCSR_FORMS, ncsr_data),  # U57c
    # U57d N-PX proxy voting record: edgar doesn't export NPX_FORMS; explicit list, matches_form
    # auto-expands to the "/A" amendment (N-PX/A)
    (["N-PX"], npx_data),  # U57d N-PX proxy voting record
    # U58 EFFECT: SEC effectiveness notice. No "/A" variant -- EFFECT is itself the terminal notice.
    # edgar parses from the primary XML (not SGML); from_xml returns None on parse failure -> data=null.
    (["EFFECT"], effect_data),  # U58 EFFECT
]


def _typed_data(filing: Filing) -> tuple[str | None, FilingData | None]:
    # obj_type and data are set together or not at all - obj_type is never advertised without data
    for forms, builder in _DATA_BUILDERS:
        if matches_form(filing, forms):
            try:
                obj = filing.obj()
            except HTTPError:
                raise  # SEC rate/transport errors surface as 429/502, never hide behind data=null
            except Exception:
                return None, None  # malformed filing artifacts -> envelope still serves, data null
            if obj is None:
                return None, None
            # a builder bug propagates (loud 500), surfaced by the parity + integration gates.
            if builder is form_d_data:
                data = form_d_data(obj, filing.xml())
            else:
                data = builder(obj)
            return type(obj).__name__, data
    return None, None


def filing_envelope(filing: Filing) -> FilingEnvelope:
    sgml = filing.sgml()
    filing_date = to_date(filing.filing_date)
    if filing_date is None:
        # every index row and feed entry carries a filing date; absence means the lookup broke
        raise ValueError(f"filing {filing.accession_no} has no filing date")
    obj_type, data = _typed_data(filing)
    return FilingEnvelope(
        accession_number=filing.accession_no,
        form=filing.form,
        cik=pad_cik(filing.cik),
        company=to_str(filing.company),
        filing_date=filing_date,
        is_multi_entity=filing.is_multi_entity,
        entities=_entities(filing, filing_date),
        header=header_model(sgml.header),
        primary_documents=[document_ref(a) for a in sgml.attachments.primary_documents],
        homepage_url=filing.homepage_url,
        text_url=filing.text_url,
        obj_type=obj_type,
        data=data,
    )
