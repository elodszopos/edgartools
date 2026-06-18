"""Form D (U50): edgar `FormD` + the offering XML -> `FormDData`, explicit field-by-field.

The offering block is a tree of small pydantic/plain objects (issuer, related persons, industry,
amounts, investors, sales compensation, signatures). Dollar amounts and counts arrive as as-filed
strings (`child_text`), kept raw so non-numeric placeholders like "Indefinite" survive. A
sales-compensation recipient carries the associated broker-dealer name (null when filed empty), the
address (with zipcode), and the foreignSolicitation flag.

edgar's `FormD` drops several fields: the issuerList co-issuers entirely, the related-person roles /
clarification / middle name, and each recipient's foreignSolicitation flag. Those entities are built
straight from the offering XML here (the same primary-document XML edgar's `FormD.from_xml` consumes),
reusing edgar's own per-element parsers (`Issuer.from_xml`, `SalesCompensationRecipient.from_xml`).
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup
from edgar._party import Address as EdgarAddress
from edgar._party import Issuer
from edgar.offerings.formd import SalesCompensationRecipient
from edgar.xmltools import child_text

from app.cik import pad_cik
from app.models.common import Address as WireAddress
from app.models.forms.formd import (
    FormDBusinessCombination,
    FormDData,
    FormDIndustryGroup,
    FormDInvestmentFundInfo,
    FormDInvestors,
    FormDIssuer,
    FormDOffering,
    FormDOfferingSalesAmounts,
    FormDPerson,
    FormDSalesCommissionFindersFees,
    FormDSalesCompensationRecipient,
    FormDSignature,
    FormDSignatureBlock,
    FormDUseOfProceeds,
)
from app.serialize import to_str


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


def _issuer(issuer: Any) -> FormDIssuer | None:
    if issuer is None:
        return None
    cik = to_str(issuer.cik)
    return FormDIssuer(
        cik=pad_cik(cik) if cik else None,
        entity_name=to_str(issuer.entity_name),
        entity_type=to_str(issuer.entity_type),
        primary_address=_address(issuer.primary_address),
        phone_number=to_str(issuer.phone_number),
        jurisdiction=to_str(issuer.jurisdiction),
        issuer_previous_names=[n for n in (to_str(x) for x in issuer.issuer_previous_names) if n is not None],
        edgar_previous_names=[n for n in (to_str(x) for x in issuer.edgar_previous_names) if n is not None],
        year_of_incorporation=to_str(issuer.year_of_incorporation),
        incorporated_within_5_years=_opt_bool(issuer.incorporated_within_5_years),
    )


def _opt_bool(value: Any) -> bool | None:
    # edgar leaves several flags as None when the source block is absent (e.g. `Tag and ...` short-
    # circuits to None); keep that three-state (true/false/absent) faithfully, never coerce None->False
    return None if value is None else bool(value)


def _additional_issuers(root: Any) -> list[FormDIssuer]:
    # co-issuers live only in <issuerList>; edgar's FormD exposes just the primary issuer, so parse
    # each co-issuer element through edgar's own Issuer.from_xml and map it like the primary issuer
    if root is None:
        return []
    issuer_list_el = root.find("issuerList")
    if issuer_list_el is None:
        return []
    mapped = (_issuer(Issuer.from_xml(el)) for el in issuer_list_el.find_all("issuer"))
    return [fi for fi in mapped if fi is not None]


def _person_address(address_el: Any) -> WireAddress | None:
    # mirror edgar's relatedPersonAddress tag mapping, then run it through the canonical wire mapping
    if address_el is None:
        return None
    return _address(
        EdgarAddress(
            street1=child_text(address_el, "street1"),
            street2=child_text(address_el, "street2"),
            city=child_text(address_el, "city"),
            state_or_country=child_text(address_el, "stateOrCountry"),
            state_or_country_description=child_text(address_el, "stateOrCountryDescription"),
            zipcode=child_text(address_el, "zipCode"),
        )
    )


def _related_persons(root: Any) -> list[FormDPerson]:
    # edgar's related-person parse drops roles, the role clarification, and the middle name, so each
    # person is built straight from its relatedPersonInfo element
    related_list_el = root.find("relatedPersonsList") if root is not None else None
    info_els = related_list_el.find_all("relatedPersonInfo") if related_list_el is not None else []
    return [_person(info_el) for info_el in info_els]


def _person(info_el: Any) -> FormDPerson:
    name_el = info_el.find("relatedPersonName")
    relationship_list_el = info_el.find("relatedPersonRelationshipList")
    relationships = [el.text for el in relationship_list_el.find_all("relationship")] if relationship_list_el is not None else []
    return FormDPerson(
        first_name=to_str(child_text(name_el, "firstName")) if name_el is not None else None,
        middle_name=to_str(child_text(name_el, "middleName")) if name_el is not None else None,
        last_name=to_str(child_text(name_el, "lastName")) if name_el is not None else None,
        address=_person_address(info_el.find("relatedPersonAddress")),
        relationships=[r for r in (to_str(x) for x in relationships) if r is not None],
        relationship_clarification=to_str(child_text(info_el, "relationshipClarification")),
    )


def _industry_group(group: Any) -> FormDIndustryGroup | None:
    if group is None:
        return None
    info = group.investment_fund_info
    return FormDIndustryGroup(
        industry_group_type=to_str(group.industry_group_type),
        investment_fund_info=(
            FormDInvestmentFundInfo(
                investment_fund_type=to_str(info.investment_fund_type),
                is_40_act=bool(info.is_40_act),
            )
            if info is not None
            else None
        ),
    )


def _business_combination(combo: Any) -> FormDBusinessCombination | None:
    if combo is None:
        return None
    return FormDBusinessCombination(
        is_business_combination=bool(combo.is_business_combination),
        clarification_of_response=to_str(combo.clarification_of_response),
    )


def _offering_sales_amounts(amounts: Any) -> FormDOfferingSalesAmounts | None:
    if amounts is None:
        return None
    return FormDOfferingSalesAmounts(
        total_offering_amount=to_str(amounts.total_offering_amount),
        total_amount_sold=to_str(amounts.total_amount_sold),
        total_remaining=to_str(amounts.total_remaining),
        clarification_of_response=to_str(amounts.clarification_of_response),
    )


def _investors(investors: Any) -> FormDInvestors | None:
    if investors is None:
        return None
    return FormDInvestors(
        has_non_accredited_investors=bool(investors.has_non_accredited_investors),
        total_already_invested=to_str(investors.total_already_invested),
    )


def _sales_commission(fees: Any) -> FormDSalesCommissionFindersFees | None:
    if fees is None:
        return None
    return FormDSalesCommissionFindersFees(
        sales_commission=to_str(fees.sales_commission),
        finders_fees=to_str(fees.finders_fees),
        clarification_of_response=to_str(fees.clarification_of_response),
    )


def _use_of_proceeds(use: Any) -> FormDUseOfProceeds | None:
    if use is None:
        return None
    return FormDUseOfProceeds(
        gross_proceeds_used=to_str(use.gross_proceeds_used),
        clarification_of_response=to_str(use.clarification_of_response),
    )


def _recipient(recipient: Any, recipient_el: Any) -> FormDSalesCompensationRecipient:
    # edgar's SalesCompensationRecipient drops the per-recipient foreignSolicitation flag; recover it
    # from the recipient element (true/false; None when the element is absent)
    foreign_text = child_text(recipient_el, "foreignSolicitation") if recipient_el is not None else None
    foreign_solicitation = None if foreign_text is None else foreign_text == "true"
    return FormDSalesCompensationRecipient(
        name=to_str(recipient.name),
        crd=to_str(recipient.crd),
        associated_bd_name=to_str(recipient.associated_bd_name),
        associated_bd_crd=to_str(recipient.associated_bd_crd),
        address=_address(recipient.address),
        foreign_solicitation=foreign_solicitation,
        states_of_solicitation=[s for s in (to_str(x) for x in recipient.states_of_solicitation or []) if s is not None],
    )


def _signature(sig: Any) -> FormDSignature:
    return FormDSignature(
        issuer_name=to_str(sig.issuer_name),
        signature_name=to_str(sig.signature_name),
        name_of_signer=to_str(sig.name_of_signer),
        title=to_str(sig.title),
        date=to_str(sig.date),
    )


def _signature_block(block: Any) -> FormDSignatureBlock | None:
    if block is None:
        return None
    return FormDSignatureBlock(
        authorized_representative=bool(block.authorized_representative),
        signatures=[_signature(s) for s in block.signatures or []],
    )


def _recipients(root: Any) -> list[FormDSalesCompensationRecipient]:
    # edgar drops each recipient's foreignSolicitation flag, so build recipients from the XML: edgar's
    # own SalesCompensationRecipient.from_xml handles every other field, the flag comes off the element
    offering_el = root.find("offeringData") if root is not None else None
    sales_comp_el = offering_el.find("salesCompensationList") if offering_el is not None else None
    recipient_els = sales_comp_el.find_all("recipient") if sales_comp_el is not None else []
    return [_recipient(SalesCompensationRecipient.from_xml(el), el) for el in recipient_els]


def _offering(od: Any, root: Any) -> FormDOffering:
    return FormDOffering(
        industry_group=_industry_group(od.industry_group),
        revenue_range=to_str(od.revenue_range),
        federal_exemptions=[e for e in (to_str(x) for x in od.federal_exemptions) if e is not None],
        # edgar's OfferingData.is_new attribute holds the <isAmendment> flag (inverted name); the true
        # meaning is captured here. Verified empirically against a D vs D/A pair (see test_formd.py).
        is_amendment=_opt_bool(od.is_new),
        date_of_first_sale=to_str(od.date_of_first_sale),
        more_than_one_year=_opt_bool(od.more_than_one_year),
        is_equity=bool(od.is_equity),
        is_pooled_investment=bool(od.is_pooled_investment),
        business_combination=_business_combination(od.business_combination_transaction),
        minimum_investment=to_str(od.minimum_investment),
        sales_compensation_recipients=_recipients(root),
        offering_sales_amounts=_offering_sales_amounts(od.offering_sales_amounts),
        investors=_investors(od.investors),
        sales_commission_finders_fees=_sales_commission(od.sales_commission_finders_fees),
        use_of_proceeds=_use_of_proceeds(od.use_of_proceeds),
    )


def form_d_data(obj: Any, offering_xml: str | None) -> FormDData:
    # offering_xml is the raw primary-document XML edgar's FormD.from_xml consumes; it is the only
    # source for the co-issuers, related-person roles, and foreignSolicitation flag edgar drops
    root = BeautifulSoup(offering_xml, "xml").find("edgarSubmission") if offering_xml else None
    return FormDData(
        submission_type=to_str(obj.submission_type) or "D",
        is_live=bool(obj.is_live),
        primary_issuer=_issuer(obj.primary_issuer),
        additional_issuers=_additional_issuers(root),
        related_persons=_related_persons(root),
        offering=_offering(obj.offering_data, root),
        signatures=_signature_block(obj.signature_block),
        is_new=bool(obj.is_new),
    )
