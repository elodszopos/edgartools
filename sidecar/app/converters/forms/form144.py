"""Form 144 (U49): edgar `Form144` -> `Form144Data`, explicit field-by-field.

The three securities tables live on the object as DataFrames whose rows carry the broker and seller
addresses. edgartools' analytical layer (totals/percentages/holding-period/10b5-1/anomaly properties)
is derived from these rows and is excluded -- the wire carries the raw, as-filed rows so consumers
derive their own metrics. Dates stay as-filed MM/DD/YYYY strings.
"""

from __future__ import annotations

from typing import Any

from app.cik import pad_cik
from app.models.common import Address as WireAddress
from app.models.forms.form144 import (
    Form144AcquisitionDetail,
    Form144Contact,
    Form144Data,
    Form144Filer,
    Form144PriorSale,
    Form144SecurityInfo,
    Form144Signature,
)
from app.serialize import to_float, to_int, to_str


def _address(address: Any) -> WireAddress | None:
    if address is None:
        return None
    return WireAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        # the form's issuerAddress DOES carry the country description (the SGML header does not)
        state_or_country_description=to_str(address.state_or_country_description),
        zipcode=to_str(address.zipcode),
    )


def _filer(filer: Any) -> Form144Filer | None:
    if filer is None:
        return None
    cik = to_str(filer.cik)
    return Form144Filer(
        cik=pad_cik(cik) if cik else None,
        name=to_str(filer.entity_name),
        file_number=to_str(filer.file_number),
    )


def _contact(contact: Any) -> Form144Contact | None:
    if contact is None:
        return None
    return Form144Contact(
        name=to_str(contact.name),
        phone=to_str(contact.phone_number),
        email=to_str(contact.email),
    )


def _security_info(rows: Any) -> list[Form144SecurityInfo]:
    # rows is a DataFrame whose columns are SecuritiesInformation.to_dict() keys; empty -> []
    return [
        Form144SecurityInfo(
            security_class=to_str(r.get("security_class")),
            units_to_be_sold=to_int(r.get("units_to_be_sold")),
            market_value=to_float(r.get("market_value")),
            units_outstanding=to_int(r.get("units_outstanding")),
            approx_sale_date=to_str(r.get("approx_sale_date")),
            exchange_name=to_str(r.get("exchange_name")),
            broker_name=to_str(r.get("broker_name")),
            broker_address=_address(r.get("broker_address")),
        )
        for r in rows.to_dict("records")
    ]


def _acquisitions(rows: Any) -> list[Form144AcquisitionDetail]:
    return [
        Form144AcquisitionDetail(
            security_class=to_str(r.get("security_class")),
            acquired_date=to_str(r.get("acquired_date")),
            amount_acquired=to_int(r.get("amount_acquired")),
            nature_of_acquisition=to_str(r.get("nature_of_acquisition")),
            acquired_from=to_str(r.get("acquired_from")),
            nature_of_payment=to_str(r.get("nature_of_payment")),
            is_gift=to_str(r.get("is_gift")),
            donor_acquired_date=to_str(r.get("donar_acquired_date")),  # edgar tag is misspelled 'donar'
            payment_date=to_str(r.get("payment_date")),
        )
        for r in rows.to_dict("records")
    ]


def _prior_sales(rows: Any) -> list[Form144PriorSale]:
    return [
        Form144PriorSale(
            security_class=to_str(r.get("security_class")),
            seller_name=to_str(r.get("seller_name")),
            sale_date=to_str(r.get("sale_date")),
            amount_sold=to_int(r.get("amount_sold")),
            gross_proceeds=to_float(r.get("gross_proceeds")),
            seller_address=_address(r.get("seller_address")),
        )
        for r in rows.to_dict("records")
    ]


def _signature(sig: Any) -> Form144Signature | None:
    if sig is None:
        return None
    return Form144Signature(
        notice_date=to_str(sig.notice_date),
        plan_adoption_dates=[d for d in (to_str(x) for x in sig.plan_adoption_dates) if d is not None],
        signature=to_str(sig.signature),
    )


def form_144_data(obj: Any) -> Form144Data:
    issuer_cik = to_str(obj.issuer_cik)
    # filing_date is a date or str from the Filing object
    _fd = obj.filing_date
    filing_date = str(_fd) if _fd is not None else None
    return Form144Data(
        form="144/A" if obj.is_amendment else "144",
        is_amendment=bool(obj.is_amendment),
        filing_date=filing_date,
        issuer_cik=pad_cik(issuer_cik) if issuer_cik else None,
        issuer_name=to_str(obj.issuer_name),
        sec_file_number=to_str(obj.sec_file_number),
        issuer_contact_phone=to_str(obj.issuer_contact_phone),
        issuer_address=_address(obj.address),
        person_selling=to_str(obj.person_selling),
        relationships=[r for r in (to_str(x) for x in obj.relationships) if r is not None],
        filer=_filer(obj.filer),
        contact=_contact(obj.contact),
        securities_information=_security_info(obj.securities_information),
        securities_to_be_sold=_acquisitions(obj.securities_to_be_sold),
        securities_sold_past_3_months=_prior_sales(obj.securities_sold_past_3_months),
        nothing_to_report=bool(obj.nothing_to_report),
        remarks=to_str(obj.remarks),
        notice_signature=_signature(obj.notice_signature),
        # aggregation scalars
        num_securities=to_int(obj.num_securities),
        is_multi_security=bool(obj.is_multi_security),
        total_units_to_be_sold=to_int(obj.total_units_to_be_sold),
        total_market_value=to_float(obj.total_market_value),
        total_amount_acquired=to_int(obj.total_amount_acquired),
        total_amount_sold_past_3_months=to_int(obj.total_amount_sold_past_3_months),
        total_gross_proceeds_past_3_months=to_float(obj.total_gross_proceeds_past_3_months),
        avg_price_per_unit=to_float(obj.avg_price_per_unit),
        percent_of_holdings=to_float(obj.percent_of_holdings),
        # single-security convenience accessors
        units_to_be_sold=to_int(obj.units_to_be_sold),
        market_value=to_float(obj.market_value),
        approx_sale_date=to_str(obj.approx_sale_date),
        security_class=to_str(obj.security_class),
        broker_name=to_str(obj.broker_name),
        exchange_name=to_str(obj.exchange_name),
        # holding-period analytics
        holding_period_days=to_int(obj.holding_period_days),
        holding_period_years=to_float(obj.holding_period_years),
        # 10b5-1 plan and compliance
        is_10b5_1_plan=bool(obj.is_10b5_1_plan),
        has_multiple_plans=bool(obj.has_multiple_plans),
        days_since_plan_adoption=to_int(obj.days_since_plan_adoption),
        cooling_off_compliant=obj.cooling_off_compliant,  # already Optional[bool]
        # anomaly detection
        is_short_hold=bool(obj.is_short_hold),
        is_large_liquidation=bool(obj.is_large_liquidation),
        anomaly_flags=list(obj.anomaly_flags),
    )
