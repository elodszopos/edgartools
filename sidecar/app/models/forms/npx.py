"""U57d wire models: N-PX / N-PX/A (+/A) proxy voting record -> kind=npx.

N-PX is filed annually by registered investment companies (mutual funds) and institutional
managers to report their proxy voting record. FUND VOTING REPORTs carry series/class registry
and vote records; INSTITUTIONAL MANAGER NOTICE REPORTs carry metadata only (proxy_votes=[]).
A single filing can contain tens of thousands of vote records (large fund families).

Each proxy_vote is one matter voted on: issuer + meeting + description + how the fund voted.
vote_categories classify the matter (DIRECTOR ELECTIONS, SAY-ON-PAY, etc.); vote_records
carry the actual vote (FOR/AGAINST/ABSTAIN + shares). Administrative EDGAR submission fields
(live_test_flag, confidential_treatment, etc.) are mirrored as-filed.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import CIK_PATTERN, WireModel


class NpxVoteCategory(WireModel):
    category_type: str


class NpxVoteRecord(WireModel):
    how_voted: str
    shares_voted: float
    management_recommendation: str


class NpxProxyVote(WireModel):
    issuer_name: str
    meeting_date: str | None
    vote_description: str
    shares_voted: float
    shares_on_loan: float
    cusip: str | None
    isin: str | None
    figi: str | None
    other_vote_description: str | None
    vote_source: str | None
    vote_series: str | None
    vote_other_info: str | None
    vote_categories: list[NpxVoteCategory]
    vote_records: list[NpxVoteRecord]
    other_managers: list[str]


class NpxIncludedManager(WireModel):
    serial_no: str
    form13f_file_number: str | None
    name: str
    sec_file_number: str | None


class NpxClassInfo(WireModel):
    class_id: str


class NpxReportSeriesClassInfo(WireModel):
    series_id: str
    class_infos: list[NpxClassInfo]


class NpxSeriesReport(WireModel):
    id_of_series: str
    name_of_series: str | None
    lei_of_series: str | None


class NpxData(WireModel):
    kind: Literal["npx"] = "npx"
    form: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    fund_name: str | None
    period_of_report: str | None
    report_calendar_year: str | None
    submission_type: str | None
    is_amendment: bool
    report_type: str | None
    address: str | None
    phone_number: str | None
    agent_for_service_name: str | None
    agent_for_service_address: str | None
    agent_for_service_address_street1: str | None
    agent_for_service_address_street2: str | None
    agent_for_service_address_city: str | None
    agent_for_service_address_state_country: str | None
    agent_for_service_address_zip_code: str | None
    signer_name: str | None
    signer_title: str | None
    signature_date: str | None
    tx_printed_signature: str | None
    crd_number: str | None
    filer_sec_file_number: str | None
    lei_number: str | None
    npx_file_number: str | None
    confidential_treatment: str | None
    notice_explanation: str | None
    explanatory_choice: str | None
    other_included_managers_count: str | None
    investment_company_type: str | None
    series_count: str | None
    registrant_type: str | None
    year_or_quarter: str | None
    amendment_no: str | None
    amendment_type: str | None
    de_novo_request_choice: str | None
    conf_denied_expired: str | None
    live_test_flag: str | None
    contact_name: str | None
    contact_phone_number: str | None
    contact_email_address: str | None
    included_managers: list[NpxIncludedManager]
    report_series_class_infos: list[NpxReportSeriesClassInfo]
    series_reports: list[NpxSeriesReport]
    proxy_votes: list[NpxProxyVote]
