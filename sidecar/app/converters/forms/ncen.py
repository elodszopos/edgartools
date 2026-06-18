"""U57b converter: edgar.funds.ncen.FundCensus -> NcenData, explicit field-by-field.

Maps the five stored structures; "Y"/"N" flags -> bool, is_diversified stays tri-state bool|None.
Two per-series facts absent from FundCensus are recovered from the public Filing: share classes from
the SGML header (filing.header.text, via app.sgml_series), joined by series id; and ALL line-of-credit
facilities re-parsed from filing.xml() (edgar's LineOfCredit keeps only the first lineOfCreditDetail).
"""

from __future__ import annotations

from decimal import Decimal

from edgar.funds.ncen import (
    Accountant,
    AuthorizedParticipant,
    BrokerDealer,
    Director,
    ETFInfo,
    FundCensus,
    FundSeriesInfo,
    LineOfCredit,
    LiquidityProvider,
    PrincipalTransaction,
    RegistrantInfo,
    SecuritiesLending,
    ServiceProvider,
    SignatureInfo,
)
from lxml import etree

from app.cik import pad_cik
from app.models.forms.ncen import (
    NcenAccountant,
    NcenAuthorizedParticipant,
    NcenBrokerDealer,
    NcenData,
    NcenDirector,
    NcenETFInfo,
    NcenFundSeriesInfo,
    NcenLineOfCredit,
    NcenLineOfCreditFacility,
    NcenLiquidityProvider,
    NcenPrincipalTransaction,
    NcenRegistrantInfo,
    NcenSecuritiesLending,
    NcenServiceProvider,
    NcenShareClass,
    NcenSignatureInfo,
)
from app.serialize import to_float, to_int, to_str
from app.sgml_series import ClassContract, parse_series_classes

# --- line-of-credit recovery (re-parsed from the primary N-CEN XML) ---------


def _strip_ns(root: etree._Element) -> None:
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str) and "}" in tag:
            el.tag = tag.split("}", 1)[1]


def _xml_text(parent: etree._Element | None, tag: str) -> str | None:
    if parent is None:
        return None
    el = parent.find(tag)
    return el.text.strip() if el is not None and el.text else None


def _xml_decimal(parent: etree._Element | None, tag: str) -> Decimal | None:
    text = _xml_text(parent, tag)
    if not text:
        return None
    try:
        return Decimal(text)
    except (ValueError, TypeError, ArithmeticError):
        return None


def _ncen_root(xml: str) -> etree._Element:
    xml_bytes = xml.encode("utf-8")
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        root = etree.fromstring(xml_bytes, parser=etree.XMLParser(recover=True))
    _strip_ns(root)
    if root.tag != "edgarSubmission":
        found = root.find(".//edgarSubmission")
        if found is not None:
            root = found
    return root


def _facilities_by_series(xml: str | None) -> dict[str, list[NcenLineOfCreditFacility]]:
    """series id -> ALL its line-of-credit facilities (committed + uncommitted)."""
    by_series: dict[str, list[NcenLineOfCreditFacility]] = {}
    if not xml:
        return by_series
    form_data = _ncen_root(xml).find("formData")
    mgmt = form_data.find("managementInvestmentQuestionSeriesInfo") if form_data is not None else None
    if mgmt is None:
        return by_series
    for question in mgmt.findall("managementInvestmentQuestion"):
        series_id = _xml_text(question, "mgmtInvSeriesId")
        loc = question.find("lineOfCredit")
        if not series_id or loc is None:
            continue
        facilities: list[NcenLineOfCreditFacility] = []
        details = loc.find("lineOfCreditDetails")
        for detail in details.findall("lineOfCreditDetail") if details is not None else []:
            institutions = detail.find("lineOfCreditInstitutions")
            names = [
                inst.get("creditInstitutionName")
                for inst in (institutions.findall("lineOfCreditInstitution") if institutions is not None else [])
                if inst.get("creditInstitutionName")
            ]
            facilities.append(
                NcenLineOfCreditFacility(
                    is_committed=to_str(_xml_text(detail, "isCreditLineCommitted")),  # as-filed text
                    size=to_float(_xml_decimal(detail, "lineOfCreditSize")),
                    institution_names=names,
                )
            )
        by_series[series_id] = facilities
    return by_series


# --- governance / people ----------------------------------------------------


def _director(d: Director) -> NcenDirector:
    return NcenDirector(
        name=to_str(d.name),
        crd_number=to_str(d.crd_number),
        is_interested_person=d.is_interested_person,
    )


def _accountant(a: Accountant | None) -> NcenAccountant | None:
    if a is None:
        return None
    return NcenAccountant(name=to_str(a.name), pcaob_number=to_str(a.pcaob_number), lei=to_str(a.lei))


# --- per-series service providers -------------------------------------------


def _service_provider(p: ServiceProvider) -> NcenServiceProvider:
    return NcenServiceProvider(
        name=to_str(p.name),
        role=to_str(p.role),
        lei=to_str(p.lei),
        file_number=to_str(p.file_number),
        crd_number=to_str(p.crd_number),
        is_affiliated=p.is_affiliated,
    )


def _broker_dealer(b: BrokerDealer) -> NcenBrokerDealer:
    return NcenBrokerDealer(
        name=to_str(b.name),
        file_number=to_str(b.file_number),
        crd_number=to_str(b.crd_number),
        lei=to_str(b.lei),
        commission=to_float(b.commission),
    )


def _principal_transaction(pt: PrincipalTransaction) -> NcenPrincipalTransaction:
    return NcenPrincipalTransaction(
        name=to_str(pt.name),
        file_number=to_str(pt.file_number),
        crd_number=to_str(pt.crd_number),
        total_purchase_sale=to_float(pt.total_purchase_sale),
    )


def _securities_lending(sl: SecuritiesLending) -> NcenSecuritiesLending:
    return NcenSecuritiesLending(
        agent_name=to_str(sl.agent_name),
        agent_lei=to_str(sl.agent_lei),
        is_affiliated=sl.is_affiliated,
        is_indemnified=sl.is_indemnified,
    )


def _line_of_credit(loc: LineOfCredit | None, facilities: list[NcenLineOfCreditFacility]) -> NcenLineOfCredit | None:
    if loc is None:
        return None
    return NcenLineOfCredit(has_line_of_credit=loc.has_line_of_credit, facilities=facilities)


def _share_class(c: ClassContract) -> NcenShareClass:
    return NcenShareClass(
        class_id=to_str(c.class_id),
        class_name=to_str(c.class_name),
        class_ticker=to_str(c.class_ticker),  # absent ticker tag -> None
    )


def _liquidity_provider(lp: LiquidityProvider) -> NcenLiquidityProvider:
    return NcenLiquidityProvider(
        name=to_str(lp.name),
        lei=to_str(lp.lei),
        is_affiliated=lp.is_affiliated,
        asset_classes=list(lp.asset_classes),
    )


# --- ETF mechanics ----------------------------------------------------------


def _authorized_participant(ap: AuthorizedParticipant) -> NcenAuthorizedParticipant:
    return NcenAuthorizedParticipant(
        name=to_str(ap.name),
        lei=to_str(ap.lei),
        file_number=to_str(ap.file_number),
        crd_number=to_str(ap.crd_number),
        purchase_value=to_float(ap.purchase_value),
        redeem_value=to_float(ap.redeem_value),
    )


def _etf_info(etf: ETFInfo | None) -> NcenETFInfo | None:
    if etf is None:
        return None
    return NcenETFInfo(
        series_id=to_str(etf.series_id),
        fund_name=to_str(etf.fund_name),
        exchange=to_str(etf.exchange),
        ticker=to_str(etf.ticker),
        creation_unit_size=to_float(etf.creation_unit_size),
        avg_pct_purchased_in_kind=to_float(etf.avg_pct_purchased_in_kind),
        avg_pct_redeemed_in_kind=to_float(etf.avg_pct_redeemed_in_kind),
        std_dev_purchased_in_kind=to_float(etf.std_dev_purchased_in_kind),
        std_dev_redeemed_in_kind=to_float(etf.std_dev_redeemed_in_kind),
        is_in_kind=etf.is_in_kind,
        authorized_participants=[_authorized_participant(ap) for ap in etf.authorized_participants],
    )


# --- per-series census ------------------------------------------------------


def _fund_series(
    s: FundSeriesInfo,
    share_classes: list[ClassContract],
    facilities: list[NcenLineOfCreditFacility],
) -> NcenFundSeriesInfo:
    return NcenFundSeriesInfo(
        name=to_str(s.name),
        series_id=to_str(s.series_id),
        lei=to_str(s.lei),
        fund_type=to_str(s.fund_type),
        is_diversified=s.is_diversified,
        avg_net_assets=to_float(s.avg_net_assets),
        aggregate_commission=to_float(s.aggregate_commission),
        is_securities_lending=s.is_securities_lending,
        advisers=[_service_provider(p) for p in s.advisers],
        custodians=[_service_provider(p) for p in s.custodians],
        transfer_agents=[_service_provider(p) for p in s.transfer_agents],
        admins=[_service_provider(p) for p in s.admins],
        pricing_services=[_service_provider(p) for p in s.pricing_services],
        shareholder_servicing_agents=[_service_provider(p) for p in s.shareholder_servicing_agents],
        broker_dealers=[_broker_dealer(b) for b in s.broker_dealers],
        brokers=[_broker_dealer(b) for b in s.brokers],
        principal_transactions=[_principal_transaction(pt) for pt in s.principal_transactions],
        securities_lending=[_securities_lending(sl) for sl in s.securities_lending],
        line_of_credit=_line_of_credit(s.line_of_credit, facilities),
        liquidity_providers=[_liquidity_provider(lp) for lp in s.liquidity_providers],
        etf_info=_etf_info(s.etf_info),
        share_classes=[_share_class(c) for c in share_classes],
    )


# --- registrant + signature -------------------------------------------------


def _registrant(r: RegistrantInfo | None) -> NcenRegistrantInfo | None:
    if r is None:
        return None
    cik = to_str(r.cik)
    return NcenRegistrantInfo(
        name=to_str(r.name),
        cik=pad_cik(cik) if cik else None,
        lei=to_str(r.lei),
        file_number=to_str(r.file_number),
        street1=to_str(r.street1),
        street2=to_str(r.street2),
        city=to_str(r.city),
        state=to_str(r.state),
        country=to_str(r.country),
        zip_code=to_str(r.zip_code),
        phone=to_str(r.phone),
        classification_type=to_str(r.classification_type),
        total_series=to_int(r.total_series),
        directors=[_director(d) for d in r.directors],
        cco_name=to_str(r.cco_name),
        cco_crd=to_str(r.cco_crd),
        accountant=_accountant(r.accountant),
        underwriter_name=to_str(r.underwriter_name),
    )


def _signature(sig: SignatureInfo | None) -> NcenSignatureInfo | None:
    if sig is None:
        return None
    return NcenSignatureInfo(
        registrant_name=to_str(sig.registrant_name),
        signed_date=to_str(sig.signed_date),
        signer=to_str(sig.signer),
        title=to_str(sig.title),
    )


def ncen_data(obj: FundCensus) -> NcenData:
    filing = obj.filing
    header_text = filing.header.text if filing is not None else None
    facilities_by_series = _facilities_by_series(filing.xml() if filing is not None else None)
    classes_by_series = {series.series_id: series.classes for series in parse_series_classes(header_text or "") if series.series_id}
    cik = to_str(obj.cik)
    return NcenData(
        form=to_str(filing.form) if filing is not None else None,
        cik=pad_cik(cik) if cik else None,
        name=to_str(obj.name),
        series_id=to_str(obj.series_id),
        lei=to_str(obj.lei),
        classification_type=to_str(obj.classification_type),
        is_etf_company=obj.is_etf_company,
        num_series=obj.num_series,
        series_ids=list(obj.series_ids),
        total_series=to_int(obj.total_series),
        report_date=to_str(obj.report_date),
        is_period_lt_12_months=obj.is_period_lt_12_months,
        registrant=_registrant(obj.registrant),
        series=[
            _fund_series(
                s,
                classes_by_series.get(s.series_id, []),
                facilities_by_series.get(s.series_id, []),
            )
            for s in obj.series
        ],
        signature_info=_signature(obj.signature_info),
    )
