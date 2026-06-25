"""U56 converter: edgar.funds.reports.FundReport -> NPortData, explicit field-by-field.

Reads only the four stored structures (header, general_info, fund_info, investments). The
DataFrame-view methods and the cross-entity series/ticker resolvers (and the lazily-built
fund_company) are never touched -- their data IS these typed records.
"""

from __future__ import annotations

from datetime import date

from edgar.funds.models.derivatives import (
    DerivativeInfo,
    ForwardDerivative,
    FutureDerivative,
    OptionDerivative,
    SwapDerivative,
    SwaptionDerivative,
)
from edgar.funds.reports import (
    CurrentMetric,
    DebtSecurity,
    FundInfo,
    FundReport,
    GeneralInfo,
    Header,
    Identifiers,
    InvestmentOrSecurity,
    MonthlyFlow,
    MonthlyTotalReturn,
    PeriodType,
    RealizedChange,
    ReturnInfo,
    SecurityLending,
)

from app.cik import pad_cik
from app.models.forms.nport import (
    NPortCurrentMetric,
    NPortData,
    NPortDebtSecurity,
    NPortDerivativeInfo,
    NPortFilerInfo,
    NPortForwardDerivative,
    NPortFundInfo,
    NPortFutureDerivative,
    NPortGeneralInfo,
    NPortHeader,
    NPortIdentifiers,
    NPortInvestment,
    NPortIssuerCredentials,
    NPortMonthlyFlow,
    NPortMonthlyTotalReturn,
    NPortOptionDerivative,
    NPortPeriodType,
    NPortRealizedChange,
    NPortReturnInfo,
    NPortSecurityLending,
    NPortSeriesClassInfo,
    NPortSwapDerivative,
    NPortSwaptionDerivative,
)
from app.serialize import to_bool, to_date, to_float, to_str

_NA = "N/A"


def _na_float(value: object) -> float | None:
    # decimal_or_na yields a Decimal or the literal "N/A" no-number sentinel -> null
    if value is None or value == _NA:
        return None
    return to_float(value)


def _maturity(value: object) -> date | None:
    # datetime_or_na yields a datetime or the "N/A" sentinel; edgar parsed this one -> ISO date
    if value is None or value == _NA:
        return None
    return to_date(value)


# --- header -----------------------------------------------------------------


def _header(header: Header) -> NPortHeader:
    fi = header.filer_info
    ic = fi.issuer_credentials
    sci = fi.series_class_info
    return NPortHeader(
        submission_type=to_str(header.submission_type),
        is_confidential=header.is_confidential,
        filer_info=NPortFilerInfo(
            issuer_credentials=NPortIssuerCredentials(cik=to_str(ic.cik), ccc=to_str(ic.ccc)),
            series_class_info=(None if sci is None else NPortSeriesClassInfo(series_id=to_str(sci.series_id), class_id=to_str(sci.class_id))),
        ),
    )


# --- general info -----------------------------------------------------------


def _general_info(g: GeneralInfo) -> NPortGeneralInfo:
    cik = to_str(g.cik)
    return NPortGeneralInfo(
        name=to_str(g.name),
        cik=pad_cik(cik) if cik else None,
        file_number=to_str(g.file_number),
        reg_lei=to_str(g.reg_lei),
        street1=to_str(g.street1),
        street2=to_str(g.street2),
        city=to_str(g.city),
        state=to_str(g.state),
        country=to_str(g.country),
        zip_or_postal_code=to_str(g.zip_or_postal_code),
        phone=to_str(g.phone),
        series_name=to_str(g.series_name),
        series_lei=to_str(g.series_lei),
        series_id=to_str(g.series_id),
        fiscal_year_end=to_str(g.fiscal_year_end),
        rep_period_date=to_str(g.rep_period_date),
        is_final_filing=to_bool(g.is_final_filing),
    )


# --- fund info --------------------------------------------------------------


def _period_type(p: PeriodType | None) -> NPortPeriodType | None:
    if p is None:
        return None
    return NPortPeriodType(
        period_3mon=to_float(p.period3Mon),
        period_1yr=to_float(p.period1Yr),
        period_5yr=to_float(p.period5Yr),
        period_10yr=to_float(p.period10Yr),
        period_30yr=to_float(p.period30Yr),
    )


def _current_metric(cm: CurrentMetric) -> NPortCurrentMetric:
    return NPortCurrentMetric(
        currency=to_str(cm.currency),
        interest_rate_risk_dv01=_period_type(cm.intrstRtRiskdv01),
        interest_rate_risk_dv100=_period_type(cm.intrstRtRiskdv100),
    )


def _monthly_total_return(m: MonthlyTotalReturn) -> NPortMonthlyTotalReturn:
    return NPortMonthlyTotalReturn(
        class_id=to_str(m.class_id),
        return_month1=_na_float(m.return1),
        return_month2=_na_float(m.return2),
        return_month3=_na_float(m.return3),
    )


def _realized_change(r: RealizedChange | None) -> NPortRealizedChange | None:
    if r is None:
        return None
    return NPortRealizedChange(
        net_realized_gain=_na_float(r.net_realized_gain),
        net_unrealized_appreciation=_na_float(r.net_unrealized_appreciation),
    )


def _monthly_flow(f: MonthlyFlow | None) -> NPortMonthlyFlow | None:
    if f is None:
        return None
    return NPortMonthlyFlow(
        redemption=_na_float(f.redemption),
        reinvestment=_na_float(f.reinvestment),
        sales=_na_float(f.sales),
    )


def _return_info(ri: ReturnInfo | None) -> NPortReturnInfo | None:
    if ri is None:
        return None
    return NPortReturnInfo(
        monthly_total_returns=[_monthly_total_return(m) for m in ri.monthly_total_returns],
        realized_change_month1=_realized_change(ri.other_mon1),
        realized_change_month2=_realized_change(ri.other_mon2),
        realized_change_month3=_realized_change(ri.other_mon3),
    )


def _fund_info(fi: FundInfo) -> NPortFundInfo:
    return NPortFundInfo(
        total_assets=to_float(fi.total_assets),
        total_liabilities=to_float(fi.total_liabilities),
        net_assets=to_float(fi.net_assets),
        assets_attr_misc_sec=to_float(fi.assets_attr_misc_sec),
        assets_invested=to_float(fi.assets_invested),
        amt_pay_one_yr_banks_borr=to_float(fi.amt_pay_one_yr_banks_borr),
        amt_pay_one_yr_ctrld_comp=to_float(fi.amt_pay_one_yr_ctrld_comp),
        amt_pay_one_yr_oth_affil=to_float(fi.amt_pay_one_yr_oth_affil),
        amt_pay_one_yr_other=to_float(fi.amt_pay_one_yr_other),
        amt_pay_aft_one_yr_banks_borr=to_float(fi.amt_pay_aft_one_yr_banks_borr),
        amt_pay_aft_one_yr_ctrld_comp=to_float(fi.amt_pay_aft_one_yr_ctrld_comp),
        amt_pay_aft_one_yr_oth_affil=to_float(fi.amt_pay_aft_one_yr_oth_affil),
        amt_pay_aft_one_yr_other=to_float(fi.amt_pay_aft_one_yr_other),
        delay_deliv=to_float(fi.delay_deliv),
        stand_by_commit=to_float(fi.stand_by_commit),
        liquidity_pref=to_float(fi.liquidity_pref),
        cash_not_report_in_cor_d=to_float(fi.cash_not_report_in_cor_d),
        current_metrics={k: _current_metric(v) for k, v in fi.current_metrics.items()},
        credit_spread_risk_investment_grade=_period_type(fi.credit_spread_risk_investment_grade),
        credit_spread_risk_non_investment_grade=_period_type(fi.credit_spread_risk_non_investment_grade),
        is_non_cash_collateral=to_bool(fi.is_non_cash_collateral),
        return_info=_return_info(fi.return_info),
        monthly_flow1=_monthly_flow(fi.monthly_flow1),
        monthly_flow2=_monthly_flow(fi.monthly_flow2),
        monthly_flow3=_monthly_flow(fi.monthly_flow3),
    )


# --- investments + derivatives ----------------------------------------------


def _identifiers(i: Identifiers) -> NPortIdentifiers:
    return NPortIdentifiers(
        ticker=to_str(i.ticker),
        isin=to_str(i.isin),
        other={(k or ""): to_str(v) for k, v in (i.other or {}).items()},
    )


def _debt_security(d: DebtSecurity | None) -> NPortDebtSecurity | None:
    if d is None:
        return None
    return NPortDebtSecurity(
        maturity_date=_maturity(d.maturity_date),
        coupon_kind=to_str(d.coupon_kind),
        annualized_rate=to_float(d.annualized_rate),
        is_default=d.is_default,
        are_payments_in_arrears=d.are_instrument_payents_in_arrears,
        is_paid_kind=d.is_paid_kind,
        is_mandatory_convertible=d.is_mandatory_convertible,
        is_continuing_convertible=d.is_continuing_convertible,
    )


def _security_lending(s: SecurityLending | None) -> NPortSecurityLending | None:
    if s is None:
        return None
    return NPortSecurityLending(
        is_cash_collateral=to_str(s.is_cash_collateral),
        is_non_cash_collateral=to_str(s.is_non_cash_collateral),
        is_loan_by_fund=to_str(s.is_loan_by_fund),
    )


def _forward(fw: ForwardDerivative | None) -> NPortForwardDerivative | None:
    if fw is None:
        return None
    return NPortForwardDerivative(
        counterparty_name=to_str(fw.counterparty_name),
        counterparty_lei=to_str(fw.counterparty_lei),
        currency_sold=to_str(fw.currency_sold),
        amount_sold=to_float(fw.amount_sold),
        currency_purchased=to_str(fw.currency_purchased),
        amount_purchased=to_float(fw.amount_purchased),
        settlement_date=to_str(fw.settlement_date),
        unrealized_appreciation=to_float(fw.unrealized_appreciation),
        deriv_addl_name=to_str(fw.deriv_addl_name),
        deriv_addl_lei=to_str(fw.deriv_addl_lei),
        deriv_addl_title=to_str(fw.deriv_addl_title),
        deriv_addl_cusip=to_str(fw.deriv_addl_cusip),
        deriv_addl_identifier=to_str(fw.deriv_addl_identifier),
        deriv_addl_identifier_type=to_str(fw.deriv_addl_identifier_type),
        deriv_addl_balance=to_float(fw.deriv_addl_balance),
        deriv_addl_units=to_str(fw.deriv_addl_units),
        deriv_addl_currency=to_str(fw.deriv_addl_currency),
        deriv_addl_value_usd=to_float(fw.deriv_addl_value_usd),
        deriv_addl_pct_val=to_float(fw.deriv_addl_pct_val),
        deriv_addl_asset_cat=to_str(fw.deriv_addl_asset_cat),
        deriv_addl_issuer_cat=to_str(fw.deriv_addl_issuer_cat),
        deriv_addl_inv_country=to_str(fw.deriv_addl_inv_country),
    )


def _swap(s: SwapDerivative | None) -> NPortSwapDerivative | None:
    if s is None:
        return None
    return NPortSwapDerivative(
        counterparty_name=to_str(s.counterparty_name),
        counterparty_lei=to_str(s.counterparty_lei),
        notional_amount=to_float(s.notional_amount),
        currency=to_str(s.currency),
        unrealized_appreciation=to_float(s.unrealized_appreciation),
        termination_date=to_str(s.termination_date),
        upfront_payment=to_float(s.upfront_payment),
        payment_currency=to_str(s.payment_currency),
        upfront_receipt=to_float(s.upfront_receipt),
        receipt_currency=to_str(s.receipt_currency),
        reference_entity_name=to_str(s.reference_entity_name),
        reference_entity_title=to_str(s.reference_entity_title),
        reference_entity_cusip=to_str(s.reference_entity_cusip),
        reference_entity_isin=to_str(s.reference_entity_isin),
        reference_entity_ticker=to_str(s.reference_entity_ticker),
        swap_flag=to_str(s.swap_flag),
        deriv_addl_name=to_str(s.deriv_addl_name),
        deriv_addl_lei=to_str(s.deriv_addl_lei),
        deriv_addl_title=to_str(s.deriv_addl_title),
        deriv_addl_cusip=to_str(s.deriv_addl_cusip),
        deriv_addl_identifier=to_str(s.deriv_addl_identifier),
        deriv_addl_identifier_type=to_str(s.deriv_addl_identifier_type),
        deriv_addl_balance=to_float(s.deriv_addl_balance),
        deriv_addl_units=to_str(s.deriv_addl_units),
        deriv_addl_desc_units=to_str(s.deriv_addl_desc_units),
        deriv_addl_currency=to_str(s.deriv_addl_currency),
        deriv_addl_value_usd=to_float(s.deriv_addl_value_usd),
        deriv_addl_pct_val=to_float(s.deriv_addl_pct_val),
        deriv_addl_asset_cat=to_str(s.deriv_addl_asset_cat),
        deriv_addl_issuer_cat=to_str(s.deriv_addl_issuer_cat),
        deriv_addl_inv_country=to_str(s.deriv_addl_inv_country),
        fixed_rate_receive=to_float(s.fixed_rate_receive),
        fixed_amount_receive=to_float(s.fixed_amount_receive),
        fixed_currency_receive=to_str(s.fixed_currency_receive),
        floating_index_receive=to_str(s.floating_index_receive),
        floating_spread_receive=to_float(s.floating_spread_receive),
        floating_amount_receive=to_float(s.floating_amount_receive),
        floating_currency_receive=to_str(s.floating_currency_receive),
        floating_tenor_receive=to_str(s.floating_tenor_receive),
        floating_tenor_unit_receive=to_str(s.floating_tenor_unit_receive),
        floating_reset_date_tenor_receive=to_str(s.floating_reset_date_tenor_receive),
        floating_reset_date_unit_receive=to_str(s.floating_reset_date_unit_receive),
        other_description_receive=to_str(s.other_description_receive),
        other_type_receive=to_str(s.other_type_receive),
        fixed_rate_pay=to_float(s.fixed_rate_pay),
        fixed_amount_pay=to_float(s.fixed_amount_pay),
        fixed_currency_pay=to_str(s.fixed_currency_pay),
        floating_index_pay=to_str(s.floating_index_pay),
        floating_spread_pay=to_float(s.floating_spread_pay),
        floating_amount_pay=to_float(s.floating_amount_pay),
        floating_currency_pay=to_str(s.floating_currency_pay),
        floating_tenor_pay=to_str(s.floating_tenor_pay),
        floating_tenor_unit_pay=to_str(s.floating_tenor_unit_pay),
        floating_reset_date_tenor_pay=to_str(s.floating_reset_date_tenor_pay),
        floating_reset_date_unit_pay=to_str(s.floating_reset_date_unit_pay),
        other_description_pay=to_str(s.other_description_pay),
        other_type_pay=to_str(s.other_type_pay),
    )


def _future(f: FutureDerivative | None) -> NPortFutureDerivative | None:
    if f is None:
        return None
    return NPortFutureDerivative(
        counterparty_name=to_str(f.counterparty_name),
        counterparty_lei=to_str(f.counterparty_lei),
        payoff_profile=to_str(f.payoff_profile),
        expiration_date=to_str(f.expiration_date),
        notional_amount=to_float(f.notional_amount),
        currency=to_str(f.currency),
        unrealized_appreciation=to_float(f.unrealized_appreciation),
        reference_entity_name=to_str(f.reference_entity_name),
        reference_entity_title=to_str(f.reference_entity_title),
        reference_entity_cusip=to_str(f.reference_entity_cusip),
        reference_entity_isin=to_str(f.reference_entity_isin),
        reference_entity_ticker=to_str(f.reference_entity_ticker),
        reference_entity_other_id=to_str(f.reference_entity_other_id),
        reference_entity_other_id_type=to_str(f.reference_entity_other_id_type),
    )


def _swaption(s: SwaptionDerivative | None) -> NPortSwaptionDerivative | None:
    if s is None:
        return None
    return NPortSwaptionDerivative(
        counterparty_name=to_str(s.counterparty_name),
        counterparty_lei=to_str(s.counterparty_lei),
        put_or_call=to_str(s.put_or_call),
        written_or_purchased=to_str(s.written_or_purchased),
        share_number=to_float(s.share_number),
        exercise_price=to_float(s.exercise_price),
        exercise_price_currency=to_str(s.exercise_price_currency),
        expiration_date=to_str(s.expiration_date),
        delta=to_str(s.delta),  # raw text; "XXXX" sentinel kept as-filed
        unrealized_appreciation=to_float(s.unrealized_appreciation),
        nested_swap=_swap(s.nested_swap),
    )


def _option(o: OptionDerivative | None) -> NPortOptionDerivative | None:
    if o is None:
        return None
    return NPortOptionDerivative(
        counterparty_name=to_str(o.counterparty_name),
        counterparty_lei=to_str(o.counterparty_lei),
        put_or_call=to_str(o.put_or_call),
        written_or_purchased=to_str(o.written_or_purchased),
        share_number=to_float(o.share_number),
        exercise_price=to_float(o.exercise_price),
        exercise_price_currency=to_str(o.exercise_price_currency),
        expiration_date=to_str(o.expiration_date),
        delta=to_str(o.delta),  # raw text; "XXXX" sentinel kept as-filed
        unrealized_appreciation=to_float(o.unrealized_appreciation),
        reference_entity_name=to_str(o.reference_entity_name),
        reference_entity_title=to_str(o.reference_entity_title),
        reference_entity_cusip=to_str(o.reference_entity_cusip),
        reference_entity_isin=to_str(o.reference_entity_isin),
        reference_entity_ticker=to_str(o.reference_entity_ticker),
        reference_entity_other_id=to_str(o.reference_entity_other_id),
        reference_entity_other_id_type=to_str(o.reference_entity_other_id_type),
        index_name=to_str(o.index_name),
        index_identifier=to_str(o.index_identifier),
        nested_forward=_forward(o.nested_forward),
        nested_future=_future(o.nested_future),
        nested_swap=_swap(o.nested_swap),
    )


def _derivative_info(di: DerivativeInfo | None) -> NPortDerivativeInfo | None:
    if di is None:
        return None
    return NPortDerivativeInfo(
        derivative_category=to_str(di.derivative_category),
        forward_derivative=_forward(di.forward_derivative),
        swap_derivative=_swap(di.swap_derivative),
        future_derivative=_future(di.future_derivative),
        option_derivative=_option(di.option_derivative),
        swaption_derivative=_swaption(di.swaption_derivative),
    )


def _investment(inv: InvestmentOrSecurity) -> NPortInvestment:
    return NPortInvestment(
        name=to_str(inv.name),
        lei=to_str(inv.lei),
        title=to_str(inv.title),
        cusip=to_str(inv.cusip),
        identifiers=_identifiers(inv.identifiers),
        balance=to_float(inv.balance),
        units=to_str(inv.units),
        desc_other_units=to_str(inv.desc_other_units),
        currency_code=to_str(inv.currency_code),
        currency_conditional_code=to_str(inv.currency_conditional_code),
        exchange_rate=to_float(inv.exchange_rate),
        value_usd=to_float(inv.value_usd),
        pct_value=to_float(inv.pct_value),
        payoff_profile=to_str(inv.payoff_profile),
        asset_category=to_str(inv.asset_category),
        issuer_category=to_str(inv.issuer_category),
        investment_country=to_str(inv.investment_country),
        is_restricted_security=inv.is_restricted_security,
        fair_value_level=to_str(inv.fair_value_level),
        debt_security=_debt_security(inv.debt_security),
        security_lending=_security_lending(inv.security_lending),
        derivative_info=_derivative_info(inv.derivative_info),
    )


def nport_data(obj: FundReport) -> NPortData:
    filing = obj.filing
    cik = to_str(obj.cik)
    return NPortData(
        form=to_str(filing.form) if filing is not None else None,
        cik=pad_cik(cik) if cik else None,
        name=to_str(obj.general_info.name) if obj.general_info.series_name is None else to_str(obj.name),
        series_id=to_str(obj.series_id),
        reporting_period=to_str(obj.reporting_period),
        has_investments=obj.has_investments,
        header=_header(obj.header),
        general_info=_general_info(obj.general_info),
        fund_info=_fund_info(obj.fund_info),
        investments=[_investment(inv) for inv in obj.investments],
        derivatives=[_investment(inv) for inv in obj.derivatives],
        non_derivatives=[_investment(inv) for inv in obj.non_derivatives],
    )
