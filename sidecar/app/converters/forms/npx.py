"""U57d converter: edgar.npx.npx.NPX -> NpxData, explicit field-by-field.

NPX delegates every property to its internal PrimaryDoc dataclass; the converter reads the
public NPX properties (not _primary_doc directly). proxy_votes is Optional[ProxyVotes] -- None
for notice reports; wire sends []. The address and agent_for_service_address properties are
computed concats on NPX (street1 + street2 + city,state,zip) -- read them directly.
"""

from __future__ import annotations

from edgar.npx.npx import NPX

from app.cik import pad_cik
from app.models.forms.npx import (
    NpxClassInfo,
    NpxData,
    NpxIncludedManager,
    NpxProxyVote,
    NpxReportSeriesClassInfo,
    NpxSeriesReport,
    NpxVoteCategory,
    NpxVoteRecord,
)
from app.serialize import to_float, to_str


def _vote_category(vc) -> NpxVoteCategory:
    return NpxVoteCategory(category_type=vc.category_type)


def _vote_record(vr) -> NpxVoteRecord:
    return NpxVoteRecord(
        how_voted=vr.how_voted,
        shares_voted=float(vr.shares_voted),
        management_recommendation=vr.management_recommendation,
    )


def _proxy_vote(pv) -> NpxProxyVote:
    return NpxProxyVote(
        issuer_name=pv.issuer_name,
        meeting_date=to_str(pv.meeting_date),
        vote_description=pv.vote_description,
        shares_voted=float(pv.shares_voted),
        shares_on_loan=float(pv.shares_on_loan),
        cusip=to_str(pv.cusip),
        isin=to_str(pv.isin),
        figi=to_str(pv.figi),
        other_vote_description=to_str(pv.other_vote_description),
        vote_source=to_str(pv.vote_source),
        vote_series=to_str(pv.vote_series),
        vote_other_info=to_str(pv.vote_other_info),
        vote_categories=[_vote_category(vc) for vc in pv.vote_categories],
        vote_records=[_vote_record(vr) for vr in pv.vote_records],
        other_managers=list(pv.other_managers),
    )


def _included_manager(im) -> NpxIncludedManager:
    return NpxIncludedManager(
        serial_no=im.serial_no,
        form13f_file_number=to_str(im.form13f_file_number),
        name=im.name,
        sec_file_number=to_str(im.sec_file_number),
    )


def _class_info(ci) -> NpxClassInfo:
    return NpxClassInfo(class_id=ci.class_id)


def _report_series_class_info(rsci) -> NpxReportSeriesClassInfo:
    return NpxReportSeriesClassInfo(
        series_id=rsci.series_id,
        class_infos=[_class_info(ci) for ci in rsci.class_infos],
    )


def _series_report(sr) -> NpxSeriesReport:
    return NpxSeriesReport(
        id_of_series=sr.id_of_series,
        name_of_series=to_str(sr.name_of_series),
        lei_of_series=to_str(sr.lei_of_series),
    )


def npx_data(obj: NPX) -> NpxData:
    filing = obj.filing
    cik = to_str(obj.cik)
    return NpxData(
        form=to_str(filing.form) if filing else None,
        cik=pad_cik(cik) if cik else None,
        fund_name=to_str(obj.fund_name),
        period_of_report=to_str(obj.period_of_report),
        report_calendar_year=to_str(obj.report_calendar_year),
        submission_type=to_str(obj.submission_type),
        is_amendment=bool(obj.is_amendment),
        report_type=to_str(obj.report_type),
        address=to_str(obj.address),
        phone_number=to_str(obj.phone_number),
        agent_for_service_name=to_str(obj.agent_for_service_name),
        agent_for_service_address=to_str(obj.agent_for_service_address),
        agent_for_service_address_street1=to_str(obj.agent_for_service_address_street1),
        agent_for_service_address_street2=to_str(obj.agent_for_service_address_street2),
        agent_for_service_address_city=to_str(obj.agent_for_service_address_city),
        agent_for_service_address_state_country=to_str(obj.agent_for_service_address_state_country),
        agent_for_service_address_zip_code=to_str(obj.agent_for_service_address_zip_code),
        signer_name=to_str(obj.signer_name),
        signer_title=to_str(obj.signer_title),
        signature_date=to_str(obj.signature_date),
        tx_printed_signature=to_str(obj.tx_printed_signature),
        crd_number=to_str(obj.crd_number),
        filer_sec_file_number=to_str(obj.filer_sec_file_number),
        lei_number=to_str(obj.lei_number),
        npx_file_number=to_str(obj.npx_file_number),
        confidential_treatment=to_str(obj.confidential_treatment),
        notice_explanation=to_str(obj.notice_explanation),
        explanatory_choice=to_str(obj.explanatory_choice),
        other_included_managers_count=to_str(obj.other_included_managers_count),
        investment_company_type=to_str(obj.investment_company_type),
        series_count=to_str(obj.series_count),
        registrant_type=to_str(obj.registrant_type),
        year_or_quarter=to_str(obj.year_or_quarter),
        amendment_no=to_str(obj.amendment_no),
        amendment_type=to_str(obj.amendment_type),
        de_novo_request_choice=to_str(obj.de_novo_request_choice),
        conf_denied_expired=to_str(obj.conf_denied_expired),
        live_test_flag=to_str(obj.live_test_flag),
        contact_name=to_str(obj.contact_name),
        contact_phone_number=to_str(obj.contact_phone_number),
        contact_email_address=to_str(obj.contact_email_address),
        included_managers=[_included_manager(im) for im in obj.included_managers],
        report_series_class_infos=[_report_series_class_info(rsci) for rsci in obj.report_series_class_infos],
        series_reports=[_series_report(sr) for sr in obj.series_reports],
        proxy_votes=[_proxy_vote(pv) for pv in obj.proxy_votes] if obj.proxy_votes else [],
    )
