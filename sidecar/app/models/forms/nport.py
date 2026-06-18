"""U56 wire models: NPORT-P / NPORT-EX fund portfolio report -> one FundReport -> kind=nport.

Full-fidelity mirror of edgar.funds.reports.FundReport's four stored structures (header,
general_info, fund_info, investments[]). The DataFrame-view methods (investment_data /
securities_data / *_data) and cross-entity resolvers (get_*_series / tickers / fund_company)
are NOT wire fields -- their rows are these typed records; see the parity gate.

Value policy: every Decimal -> float|None; raw `_text` strings (incl. literal "N/A" filed
text and date-like strings edgar never parses) pass through faithfully; the decimal_or_na
numeric sentinel "N/A" -> null (it is edgar's no-number marker); DebtSecurity.maturity_date
(edgar parses it to datetime) -> ISO date string. delta is raw text ("XXXX" sentinel kept).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.common import WireModel

# --- header -----------------------------------------------------------------


class NPortIssuerCredentials(WireModel):
    cik: str | None
    ccc: str | None  # confirmation code; masked "XXXXXXXX" in public filings


class NPortSeriesClassInfo(WireModel):
    series_id: str | None
    class_id: str | None


class NPortFilerInfo(WireModel):
    issuer_credentials: NPortIssuerCredentials | None
    series_class_info: NPortSeriesClassInfo | None  # absent for single-series funds


class NPortHeader(WireModel):
    submission_type: str | None
    is_confidential: bool
    filer_info: NPortFilerInfo | None


# --- general info -----------------------------------------------------------


class NPortGeneralInfo(WireModel):
    name: str | None
    cik: str | None
    file_number: str | None
    reg_lei: str | None
    street1: str | None
    street2: str | None
    city: str | None
    state: str | None
    country: str | None
    zip_or_postal_code: str | None
    phone: str | None
    series_name: str | None
    series_lei: str | None
    series_id: str | None
    fiscal_year_end: str | None  # as-filed (edgar stores raw _text, often ISO)
    rep_period_date: str | None  # portfolio "as of" date, as-filed _text
    is_final_filing: bool | None


# --- fund info (risk metrics, returns, flows) -------------------------------


class NPortPeriodType(WireModel):
    period_3mon: float | None
    period_1yr: float | None
    period_5yr: float | None
    period_10yr: float | None
    period_30yr: float | None


class NPortCurrentMetric(WireModel):
    currency: str | None
    interest_rate_risk_dv01: NPortPeriodType | None
    interest_rate_risk_dv100: NPortPeriodType | None


class NPortMonthlyTotalReturn(WireModel):
    class_id: str | None
    return_month1: float | None  # decimal_or_na sentinel "N/A" -> null
    return_month2: float | None
    return_month3: float | None


class NPortRealizedChange(WireModel):
    net_realized_gain: float | None
    net_unrealized_appreciation: float | None


class NPortMonthlyFlow(WireModel):
    redemption: float | None
    reinvestment: float | None
    sales: float | None


class NPortReturnInfo(WireModel):
    monthly_total_returns: list[NPortMonthlyTotalReturn]
    realized_change_month1: NPortRealizedChange | None
    realized_change_month2: NPortRealizedChange | None
    realized_change_month3: NPortRealizedChange | None


class NPortFundInfo(WireModel):
    total_assets: float | None
    total_liabilities: float | None
    net_assets: float | None
    assets_attr_misc_sec: float | None
    assets_invested: float | None
    amt_pay_one_yr_banks_borr: float | None
    amt_pay_one_yr_ctrld_comp: float | None
    amt_pay_one_yr_oth_affil: float | None
    amt_pay_one_yr_other: float | None
    amt_pay_aft_one_yr_banks_borr: float | None
    amt_pay_aft_one_yr_ctrld_comp: float | None
    amt_pay_aft_one_yr_oth_affil: float | None
    amt_pay_aft_one_yr_other: float | None
    delay_deliv: float | None
    stand_by_commit: float | None
    liquidity_pref: float | None
    cash_not_report_in_cor_d: float | None
    current_metrics: dict[str, NPortCurrentMetric]  # keyed by currency code
    credit_spread_risk_investment_grade: NPortPeriodType | None
    credit_spread_risk_non_investment_grade: NPortPeriodType | None
    is_non_cash_collateral: bool | None
    return_info: NPortReturnInfo | None
    monthly_flow1: NPortMonthlyFlow | None
    monthly_flow2: NPortMonthlyFlow | None
    monthly_flow3: NPortMonthlyFlow | None


# --- investments (holdings) + derivatives -----------------------------------


class NPortIdentifiers(WireModel):
    ticker: str | None  # raw as-filed; NOT the resolved cross-reference ticker
    isin: str | None
    other: dict[str, str | None]


class NPortDebtSecurity(WireModel):
    maturity_date: date | None  # edgar-parsed datetime -> ISO date (sentinel "N/A" -> null)
    coupon_kind: str | None
    annualized_rate: float | None
    is_default: bool
    are_payments_in_arrears: bool
    is_paid_kind: bool
    is_mandatory_convertible: bool
    is_continuing_convertible: bool


class NPortSecurityLending(WireModel):
    is_cash_collateral: str | None  # "Y"/"N" as-filed text, not a bool
    is_non_cash_collateral: str | None
    is_loan_by_fund: str | None


class NPortForwardDerivative(WireModel):
    counterparty_name: str | None
    counterparty_lei: str | None
    currency_sold: str | None
    amount_sold: float | None
    currency_purchased: str | None
    amount_purchased: float | None
    settlement_date: str | None  # as-filed _text
    unrealized_appreciation: float | None
    deriv_addl_name: str | None
    deriv_addl_lei: str | None
    deriv_addl_title: str | None
    deriv_addl_cusip: str | None
    deriv_addl_identifier: str | None
    deriv_addl_identifier_type: str | None
    deriv_addl_balance: float | None
    deriv_addl_units: str | None
    deriv_addl_currency: str | None
    deriv_addl_value_usd: float | None
    deriv_addl_pct_val: float | None
    deriv_addl_asset_cat: str | None
    deriv_addl_issuer_cat: str | None
    deriv_addl_inv_country: str | None


class NPortSwapDerivative(WireModel):
    counterparty_name: str | None
    counterparty_lei: str | None
    notional_amount: float | None
    currency: str | None
    unrealized_appreciation: float | None
    termination_date: str | None  # as-filed _text
    upfront_payment: float | None
    payment_currency: str | None
    upfront_receipt: float | None
    receipt_currency: str | None
    reference_entity_name: str | None
    reference_entity_title: str | None
    reference_entity_cusip: str | None
    reference_entity_isin: str | None
    reference_entity_ticker: str | None
    swap_flag: str | None
    deriv_addl_name: str | None
    deriv_addl_lei: str | None
    deriv_addl_title: str | None
    deriv_addl_cusip: str | None
    deriv_addl_identifier: str | None
    deriv_addl_identifier_type: str | None
    deriv_addl_balance: float | None
    deriv_addl_units: str | None
    deriv_addl_desc_units: str | None
    deriv_addl_currency: str | None
    deriv_addl_value_usd: float | None
    deriv_addl_pct_val: float | None
    deriv_addl_asset_cat: str | None
    deriv_addl_issuer_cat: str | None
    deriv_addl_inv_country: str | None
    # receive leg
    fixed_rate_receive: float | None
    fixed_amount_receive: float | None
    fixed_currency_receive: str | None
    floating_index_receive: str | None
    floating_spread_receive: float | None
    floating_amount_receive: float | None
    floating_currency_receive: str | None
    floating_tenor_receive: str | None
    floating_tenor_unit_receive: str | None
    floating_reset_date_tenor_receive: str | None
    floating_reset_date_unit_receive: str | None
    other_description_receive: str | None
    other_type_receive: str | None
    # payment leg
    fixed_rate_pay: float | None
    fixed_amount_pay: float | None
    fixed_currency_pay: str | None
    floating_index_pay: str | None
    floating_spread_pay: float | None
    floating_amount_pay: float | None
    floating_currency_pay: str | None
    floating_tenor_pay: str | None
    floating_tenor_unit_pay: str | None
    floating_reset_date_tenor_pay: str | None
    floating_reset_date_unit_pay: str | None
    other_description_pay: str | None
    other_type_pay: str | None


class NPortFutureDerivative(WireModel):
    counterparty_name: str | None
    counterparty_lei: str | None
    payoff_profile: str | None
    expiration_date: str | None  # as-filed _text
    notional_amount: float | None
    currency: str | None
    unrealized_appreciation: float | None
    reference_entity_name: str | None
    reference_entity_title: str | None
    reference_entity_cusip: str | None
    reference_entity_isin: str | None
    reference_entity_ticker: str | None
    reference_entity_other_id: str | None
    reference_entity_other_id_type: str | None


class NPortSwaptionDerivative(WireModel):
    counterparty_name: str | None
    counterparty_lei: str | None
    put_or_call: str | None
    written_or_purchased: str | None
    share_number: float | None
    exercise_price: float | None
    exercise_price_currency: str | None
    expiration_date: str | None
    delta: str | None  # raw _text; numeric or "XXXX" sentinel kept as-filed
    unrealized_appreciation: float | None
    nested_swap: NPortSwapDerivative | None


class NPortOptionDerivative(WireModel):
    counterparty_name: str | None
    counterparty_lei: str | None
    put_or_call: str | None
    written_or_purchased: str | None
    share_number: float | None
    exercise_price: float | None
    exercise_price_currency: str | None
    expiration_date: str | None
    delta: str | None  # raw _text; numeric or "XXXX" sentinel kept as-filed
    unrealized_appreciation: float | None
    reference_entity_name: str | None
    reference_entity_title: str | None
    reference_entity_cusip: str | None
    reference_entity_isin: str | None
    reference_entity_ticker: str | None
    reference_entity_other_id: str | None
    reference_entity_other_id_type: str | None
    index_name: str | None
    index_identifier: str | None
    nested_forward: NPortForwardDerivative | None
    nested_future: NPortFutureDerivative | None
    nested_swap: NPortSwapDerivative | None


class NPortDerivativeInfo(WireModel):
    derivative_category: str | None  # FWD, SWP, FUT, OPT, SWO, WAR
    forward_derivative: NPortForwardDerivative | None
    swap_derivative: NPortSwapDerivative | None
    future_derivative: NPortFutureDerivative | None
    option_derivative: NPortOptionDerivative | None
    swaption_derivative: NPortSwaptionDerivative | None


class NPortInvestment(WireModel):
    name: str | None  # literal "N/A" passes through faithfully
    lei: str | None
    title: str | None
    cusip: str | None
    identifiers: NPortIdentifiers | None
    balance: float | None  # negative for short positions
    units: str | None  # NS shares / PA principal / NC contracts
    desc_other_units: str | None
    currency_code: str | None
    currency_conditional_code: str | None  # denomination currency when != reporting
    exchange_rate: float | None
    value_usd: float | None  # negative for shorts/derivatives
    pct_value: float | None
    payoff_profile: str | None  # Long/Short or literal "N/A" for derivatives
    asset_category: str | None
    issuer_category: str | None
    investment_country: str | None
    is_restricted_security: bool
    fair_value_level: str | None  # "1"/"2"/"3" as-filed text
    debt_security: NPortDebtSecurity | None
    security_lending: NPortSecurityLending | None
    derivative_info: NPortDerivativeInfo | None


class NPortData(WireModel):
    kind: Literal["nport"] = "nport"
    form: str | None
    cik: str | None
    name: str | None
    series_id: str | None
    reporting_period: str | None
    has_investments: bool | None
    header: NPortHeader | None
    general_info: NPortGeneralInfo | None
    fund_info: NPortFundInfo | None
    investments: list[NPortInvestment]
    derivatives: list[NPortInvestment]
    non_derivatives: list[NPortInvestment]
