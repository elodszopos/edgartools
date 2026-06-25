"""edgar `ThirteenF` -> typed `data` (Form 13F family), explicit field-by-field.

The cover/summary/signature come from the parsed primary document (`primary_form_information`);
holdings come from the disaggregated `infotable` DataFrame, one wire record per row. total_value
is read from the top-level `obj.total_value` (which normalizes pre-2023 thousands -> dollars), NOT
the raw `summary_page.total_value` dataclass field (era-dependent thousands). Cross-filing
properties (previous_holding_report, compare_holdings, holding_history) are not mapped -- they
require cross-filing SEC fetches excluded by the envelope own-artifacts policy.
"""

from __future__ import annotations

from typing import Any

from edgar.thirteenf import ThirteenF

from app.models.common import Address as WireAddress
from app.models.forms.thirteenf import (
    Form13FData,
    ThirteenFCoverPage,
    ThirteenFFilingManager,
    ThirteenFHolding,
    ThirteenFOtherManager,
    ThirteenFSignature,
    ThirteenFSummary,
)
from app.serialize import to_date, to_float, to_int, to_str


def _address(address: Any) -> WireAddress | None:
    if address is None:
        return None
    return WireAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        # the 13F cover-page address carries no country description (unlike the submissions store)
        state_or_country_description=to_str(getattr(address, "state_or_country_description", None)),
        zipcode=to_str(address.zipcode),
    )


def _other_manager(m: Any) -> ThirteenFOtherManager:
    return ThirteenFOtherManager(
        cik=to_str(m.cik),
        name=to_str(m.name),
        file_number=to_str(m.file_number),
        sequence_number=to_int(m.sequence_number),
    )


def _filing_manager(manager: Any) -> ThirteenFFilingManager | None:
    if manager is None:
        return None
    return ThirteenFFilingManager(name=to_str(manager.name), address=_address(manager.address))


def _cover_page(cover: Any) -> ThirteenFCoverPage:
    return ThirteenFCoverPage(
        report_calendar_or_quarter=to_str(cover.report_calendar_or_quarter),
        report_type=to_str(cover.report_type),
        filing_manager=_filing_manager(cover.filing_manager),
        other_managers=[_other_manager(m) for m in cover.other_managers or []],
    )


def _summary(obj: ThirteenF, summary: Any) -> ThirteenFSummary:
    return ThirteenFSummary(
        other_included_managers_count=to_int(summary.other_included_managers_count),
        # obj.total_value normalizes pre-2023 thousands x1000; the raw summary field does not
        total_value=to_float(obj.total_value),
        total_holdings=to_int(obj.total_holdings),
        other_managers=[_other_manager(m) for m in summary.other_managers or []],
    )


def _signature(sig: Any) -> ThirteenFSignature:
    return ThirteenFSignature(
        name=to_str(sig.name),
        title=to_str(sig.title),
        phone=to_str(sig.phone),
        signature=to_str(sig.signature),
        city=to_str(sig.city),
        state_or_country=to_str(sig.state_or_country),
        date=to_str(sig.date),
    )


def _holding(row: dict[str, Any]) -> ThirteenFHolding:
    return ThirteenFHolding(
        issuer=to_str(row.get("Issuer")),
        title_of_class=to_str(row.get("Class")),
        cusip=to_str(row.get("Cusip")),
        ticker=to_str(row.get("Ticker")),  # NaN for unmapped CUSIPs -> null
        value=to_int(row.get("Value")),  # already normalized to whole dollars
        shares_or_principal_amount=to_int(row.get("SharesPrnAmount")),
        shares_or_principal_type=to_str(row.get("Type")),
        put_call=to_str(row.get("PutCall")),  # "" for ordinary long -> null
        investment_discretion=to_str(row.get("InvestmentDiscretion")),
        other_manager=to_str(row.get("OtherManager")),
        sole_voting_authority=to_int(row.get("SoleVoting")),
        shared_voting_authority=to_int(row.get("SharedVoting")),
        no_voting_authority=to_int(row.get("NonVoting")),
    )


def _holdings(obj: ThirteenF) -> list[ThirteenFHolding]:
    # None for 13F-NT notices (no information table) and unparsed pre-2013 TXT tables
    infotable = obj.infotable
    if infotable is None or len(infotable) == 0:
        return []
    return [_holding(row) for row in infotable.to_dict(orient="records")]


def form_13f_data(obj: ThirteenF) -> Form13FData:
    primary = obj.primary_form_information  # None only for pre-2013 TXT-only filings
    # filing_date from edgar is already formatted as a string via format_date()
    _fd = obj.filing_date
    filing_date = to_str(_fd) if isinstance(_fd, str) else (str(_fd) if _fd is not None else None)
    # investment_manager returns a FilingManager dataclass; extract name for convenience
    _im = obj.investment_manager
    investment_manager_name = to_str(_im.name) if _im is not None else None
    # management_company_name is always a str (falls back to filing company name)
    mgmt_name = to_str(obj.management_company_name)
    return Form13FData(
        form=obj.form,
        report_period=to_date(obj.report_period),
        is_amendment=obj.form.endswith("/A"),
        has_holdings=bool(obj.has_infotable()),
        accession_number=to_str(obj.accession_number),
        filing_date=filing_date,
        total_holdings=to_int(obj.total_holdings),
        total_value=to_float(obj.total_value),
        cover_page=_cover_page(primary.cover_page) if primary else None,
        summary=_summary(obj, primary.summary_page) if primary else None,
        signature=_signature(primary.signature) if primary else None,
        additional_information=to_str(primary.additional_information) if primary else None,
        holdings=_holdings(obj),
        filing_signer_name=to_str(obj.filing_signer_name),
        filing_signer_title=to_str(obj.filing_signer_title),
        signer=to_str(obj.signer),
        investment_manager=investment_manager_name,
        management_company_name=mgmt_name,
        manager_name=mgmt_name,  # deprecated alias; same value, avoids DeprecationWarning
        other_managers=[_other_manager(m) for m in obj.other_managers],
        infotable_txt=to_str(obj.infotable_txt),
        infotable_xml=to_str(obj.infotable_xml),
    )
