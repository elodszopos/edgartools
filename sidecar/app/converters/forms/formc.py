"""Form C (U51): edgar `FormC` -> `FormCData`, explicit field-by-field.

The variant (`form`) drives which blocks are present: the offering + funding portal are null for the
annual report (C-AR) and termination (C-TR); the annual-report disclosure is null for C-TR. Offering
amounts arrive as floats (edgar coerces a blank to 0.0); other amounts/counts are as-filed strings.

The filer block ships the identity, the CCC submission credential (SEC-masked to "XXXXXXXX"), the
LIVE/TEST flag, the copy-routing flags, and the report period. Nothing here re-parses SEC XML - the
wire serves only what the `FormC` object exposes.
"""

from __future__ import annotations

from typing import Any

from app.cik import pad_cik
from app.models.common import Address as WireAddress
from app.models.forms.formc import (
    FormCAnnualReport,
    FormCData,
    FormCFilerInfo,
    FormCFundingPortal,
    FormCIssuer,
    FormCIssuerSignature,
    FormCOffering,
    FormCPersonSignature,
    FormCSignatureInfo,
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
        state_or_country_description=to_str(address.state_or_country_description),
        zipcode=to_str(address.zipcode),
    )


def _filer(filer: Any) -> FormCFilerInfo:
    cik = to_str(filer.cik)
    return FormCFilerInfo(
        cik=pad_cik(cik) if cik else None,
        ccc=to_str(filer.ccc),
        live_or_test=bool(filer.live_or_test),
        confirming_copy_flag=bool(filer.confirming_copy_flag),
        return_copy_flag=bool(filer.return_copy_flag),
        override_internet_flag=bool(filer.override_internet_flag),
        period=to_date(filer.period),
    )


def _funding_portal(portal: Any) -> FormCFundingPortal | None:
    if portal is None:
        return None
    cik = to_str(portal.cik)
    return FormCFundingPortal(
        name=to_str(portal.name),
        cik=pad_cik(cik) if cik else None,
        crd=to_str(portal.crd),
        file_number=to_str(portal.file_number),
    )


def _issuer(issuer: Any) -> FormCIssuer:
    return FormCIssuer(
        name=to_str(issuer.name),
        legal_status=to_str(issuer.legal_status),
        jurisdiction=to_str(issuer.jurisdiction),
        date_of_incorporation=to_date(issuer.date_of_incorporation),
        website=to_str(issuer.website),
        co_issuer=bool(issuer.co_issuer),
        address=_address(issuer.address),
        funding_portal=_funding_portal(issuer.funding_portal),
    )


def _offering(offering: Any) -> FormCOffering | None:
    if offering is None:
        return None
    return FormCOffering(
        compensation_amount=to_str(offering.compensation_amount),
        financial_interest=to_str(offering.financial_interest),
        security_offered_type=to_str(offering.security_offered_type),
        security_offered_other_desc=to_str(offering.security_offered_other_desc),
        no_of_security_offered=to_str(offering.no_of_security_offered),
        price=to_str(offering.price),
        price_determination_method=to_str(offering.price_determination_method),
        offering_amount=to_float(offering.offering_amount),
        over_subscription_accepted=to_str(offering.over_subscription_accepted),
        over_subscription_allocation_type=to_str(offering.over_subscription_allocation_type),
        desc_over_subscription=to_str(offering.desc_over_subscription),
        maximum_offering_amount=to_float(offering.maximum_offering_amount),
        deadline_date=to_date(offering.deadline_date),
    )


def _annual_report(report: Any) -> FormCAnnualReport | None:
    if report is None:
        return None
    return FormCAnnualReport(
        current_employees=to_int(report.current_employees) or 0,
        total_asset_most_recent_fiscal_year=to_float(report.total_asset_most_recent_fiscal_year) or 0.0,
        total_asset_prior_fiscal_year=to_float(report.total_asset_prior_fiscal_year) or 0.0,
        cash_equi_most_recent_fiscal_year=to_float(report.cash_equi_most_recent_fiscal_year) or 0.0,
        cash_equi_prior_fiscal_year=to_float(report.cash_equi_prior_fiscal_year) or 0.0,
        act_received_most_recent_fiscal_year=to_float(report.act_received_most_recent_fiscal_year) or 0.0,
        act_received_prior_fiscal_year=to_float(report.act_received_prior_fiscal_year) or 0.0,
        short_term_debt_most_recent_fiscal_year=to_float(report.short_term_debt_most_recent_fiscal_year) or 0.0,
        short_term_debt_prior_fiscal_year=to_float(report.short_term_debt_prior_fiscal_year) or 0.0,
        long_term_debt_most_recent_fiscal_year=to_float(report.long_term_debt_most_recent_fiscal_year) or 0.0,
        long_term_debt_prior_fiscal_year=to_float(report.long_term_debt_prior_fiscal_year) or 0.0,
        revenue_most_recent_fiscal_year=to_float(report.revenue_most_recent_fiscal_year) or 0.0,
        revenue_prior_fiscal_year=to_float(report.revenue_prior_fiscal_year) or 0.0,
        cost_goods_sold_most_recent_fiscal_year=to_float(report.cost_goods_sold_most_recent_fiscal_year) or 0.0,
        cost_goods_sold_prior_fiscal_year=to_float(report.cost_goods_sold_prior_fiscal_year) or 0.0,
        tax_paid_most_recent_fiscal_year=to_float(report.tax_paid_most_recent_fiscal_year) or 0.0,
        tax_paid_prior_fiscal_year=to_float(report.tax_paid_prior_fiscal_year) or 0.0,
        net_income_most_recent_fiscal_year=to_float(report.net_income_most_recent_fiscal_year) or 0.0,
        net_income_prior_fiscal_year=to_float(report.net_income_prior_fiscal_year) or 0.0,
        offering_jurisdictions=[s for s in (to_str(x) for x in report.offering_jurisdictions or []) if s is not None],
    )


def _person_signature(sig: Any) -> FormCPersonSignature:
    return FormCPersonSignature(
        signature=to_str(sig.signature),
        title=to_str(sig.title),
        date=to_date(sig.date),
    )


def _signature_info(info: Any) -> FormCSignatureInfo:
    issuer_sig = info.issuer_signature
    return FormCSignatureInfo(
        issuer_signature=FormCIssuerSignature(
            issuer=to_str(issuer_sig.issuer),
            title=to_str(issuer_sig.title),
            signature=to_str(issuer_sig.signature),
        ),
        signatures=[_person_signature(s) for s in info.signatures or []],
    )


def form_c_data(obj: Any) -> FormCData:
    # issuer_cik is the filer CIK (same as filer.cik); portal_cik from funding portal
    _issuer_cik = to_str(obj.issuer_cik)
    _portal_cik = to_str(obj.portal_cik)
    return FormCData(
        form=to_str(obj.form) or "C",
        filer=_filer(obj.filer_information),
        issuer=_issuer(obj.issuer_information),
        offering=_offering(obj.offering_information),
        annual_report=_annual_report(obj.annual_report_disclosure),
        signatures=_signature_info(obj.signature_info),
        issuer_cik=pad_cik(_issuer_cik) if _issuer_cik else None,
        issuer_name=to_str(obj.issuer_name),
        portal_cik=pad_cik(_portal_cik) if _portal_cik else None,
        portal_name=to_str(obj.portal_name),
        portal_file_number=to_str(obj.portal_file_number),
        description=to_str(obj.description),
        campaign_status=to_str(obj.campaign_status),
        days_to_deadline=to_int(obj.days_to_deadline) if obj.days_to_deadline is not None else None,
        is_expired=bool(obj.is_expired),
    )
