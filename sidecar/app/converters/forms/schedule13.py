"""edgar `Schedule13D`/`Schedule13G` -> typed `data`, explicit field-by-field.

The two objects share the cover-page nested types (reporting persons, issuer, security, signatures)
so those build through one set of helpers; only the narrative `items` differ (13D free-text 1-7 vs
13G flag-heavy 1-10). Numerics are edgar's already-parsed ints/floats (safe_int/safe_float, never
NaN); identity strings route through to_str so as-filed empties land as null. Pre-mandate HTML-only
filings arrive with has_structured_data=False, empty persons, and null totals - mirrored faithfully.
"""

from __future__ import annotations

from typing import Any

from edgar.beneficial_ownership import Schedule13D, Schedule13G

from app.models.common import Address as WireAddress
from app.models.forms.schedule13 import (
    Schedule13Owner,
    Schedule13DData,
    Schedule13DItems,
    Schedule13GData,
    Schedule13GItems,
    Schedule13Issuer,
    Schedule13Security,
    Schedule13Signature,
)
from app.serialize import to_date, to_iso_str, to_str


def _address(address: Any) -> WireAddress | None:
    if address is None:
        return None
    return WireAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        # the cover-page XML address carries no country description (unlike the submissions store)
        state_or_country_description=to_str(getattr(address, "state_or_country_description", None)),
        zipcode=to_str(address.zipcode),
    )


def _owner(p: Any) -> Schedule13Owner:
    return Schedule13Owner(
        cik=to_str(p.cik),  # "" on 13G / no-CIK 13D filers -> null
        name=p.name,  # required; kept raw as filed
        citizenship=to_str(p.citizenship),
        sole_voting_power=p.sole_voting_power,
        shared_voting_power=p.shared_voting_power,
        sole_dispositive_power=p.sole_dispositive_power,
        shared_dispositive_power=p.shared_dispositive_power,
        aggregate_amount=p.aggregate_amount,
        percent_of_class=p.percent_of_class,
        type_of_reporting_person=to_str(p.type_of_reporting_person),
        fund_type=to_str(p.fund_type),
        comment=to_str(p.comment),
        member_of_group=to_str(p.member_of_group),
        is_aggregate_exclude_shares=bool(p.is_aggregate_exclude_shares),
        no_cik=bool(p.no_cik),
    )


def _issuer(info: Any) -> Schedule13Issuer:
    return Schedule13Issuer(
        cik=to_str(info.cik),
        name=to_str(info.name),
        cusip=to_str(info.cusip),
        address=_address(info.address),
    )


def _security(info: Any) -> Schedule13Security:
    return Schedule13Security(title=to_str(info.title), cusip=to_str(info.cusip))


def _signature(sig: Any) -> Schedule13Signature:
    return Schedule13Signature(
        reporting_person=to_str(sig.reporting_person),
        signature=to_str(sig.signature),
        title=to_str(sig.title),
        date=to_str(sig.date),
    )


def _items_13d(it: Any) -> Schedule13DItems:
    return Schedule13DItems(
        item1_security_title=to_str(it.item1_security_title),
        item1_issuer_name=to_str(it.item1_issuer_name),
        item1_issuer_address=to_str(it.item1_issuer_address),
        item2_filing_persons=to_str(it.item2_filing_persons),
        item2_business_address=to_str(it.item2_business_address),
        item2_principal_occupation=to_str(it.item2_principal_occupation),
        item2_convictions=to_str(it.item2_convictions),
        item2_citizenship=to_str(it.item2_citizenship),
        item3_source_of_funds=to_str(it.item3_source_of_funds),
        item4_purpose_of_transaction=to_str(it.item4_purpose_of_transaction),
        item5_percentage_of_class=to_str(it.item5_percentage_of_class),
        item5_number_of_shares=to_str(it.item5_number_of_shares),
        item5_transactions=to_str(it.item5_transactions),
        item5_shareholders=to_str(it.item5_shareholders),
        item5_date_5pct_ownership=to_str(it.item5_date_5pct_ownership),
        item6_contracts=to_str(it.item6_contracts),
        item7_exhibits=to_str(it.item7_exhibits),
    )


def _items_13g(it: Any) -> Schedule13GItems:
    return Schedule13GItems(
        item1_issuer_name=to_str(it.item1_issuer_name),
        item1_issuer_address=to_str(it.item1_issuer_address),
        item2_filer_names=to_str(it.item2_filer_names),
        item2_filer_addresses=to_str(it.item2_filer_addresses),
        item2_citizenship=to_str(it.item2_citizenship),
        item3_not_applicable=bool(it.item3_not_applicable),
        item4_amount_beneficially_owned=to_str(it.item4_amount_beneficially_owned),
        item4_percent_of_class=to_str(it.item4_percent_of_class),
        item4_sole_voting=to_str(it.item4_sole_voting),
        item4_shared_voting=to_str(it.item4_shared_voting),
        item4_sole_dispositive=to_str(it.item4_sole_dispositive),
        item4_shared_dispositive=to_str(it.item4_shared_dispositive),
        item5_not_applicable=bool(it.item5_not_applicable),
        item5_ownership_5pct_or_less=to_str(it.item5_ownership_5pct_or_less),
        item6_not_applicable=bool(it.item6_not_applicable),
        item7_not_applicable=bool(it.item7_not_applicable),
        item8_not_applicable=bool(it.item8_not_applicable),
        item9_not_applicable=bool(it.item9_not_applicable),
        item10_certification=to_str(it.item10_certification),
    )


def schedule_13d_data(obj: Schedule13D) -> Schedule13DData:
    event = to_str(obj.date_of_event)
    return Schedule13DData(
        issuer=_issuer(obj.issuer_info),
        security=_security(obj.security_info),
        reporting_persons=[_owner(p) for p in obj.reporting_persons],
        items=_items_13d(obj.items),
        signatures=[_signature(s) for s in obj.signatures],
        event_date=event,
        date_of_event=event,  # edgar exposes both names for the same value
        filing_date=to_iso_str(obj.filing_date),
        previously_filed=bool(obj.previously_filed),
        is_amendment=bool(obj.is_amendment),
        amendment_number=obj.amendment_number,
        has_structured_data=bool(obj.has_structured_data),
        total_shares=obj.total_shares,
        total_percent=obj.total_percent,
    )


def schedule_13g_data(obj: Schedule13G) -> Schedule13GData:
    event = to_str(obj.event_date)
    return Schedule13GData(
        issuer=_issuer(obj.issuer_info),
        security=_security(obj.security_info),
        reporting_persons=[_owner(p) for p in obj.reporting_persons],
        items=_items_13g(obj.items),
        signatures=[_signature(s) for s in obj.signatures],
        event_date=event,
        date_of_event=event,  # edgar exposes both names for the same value
        filing_date=to_iso_str(obj.filing_date),
        rule_designation=to_str(obj.rule_designation),
        is_passive_investor=bool(obj.is_passive_investor),
        is_amendment=bool(obj.is_amendment),
        amendment_number=obj.amendment_number,
        has_structured_data=bool(obj.has_structured_data),
        total_shares=obj.total_shares,
        total_percent=obj.total_percent,
    )
