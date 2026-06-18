"""U57a wire models: N-MFP2 / N-MFP3 money market fund monthly portfolio report -> one
MoneyMarketFund -> kind=nmfp.

Full-fidelity mirror of edgar.funds.nmfp3.MoneyMarketFund's four stored structures (general_info,
series_info, share_classes[], securities[]). The DataFrame-view methods (portfolio_data /
share_class_data / *_history / collateral_data / holdings_by_category) and the derived scalar
properties (cik / name / net_assets / num_*) are NOT wire fields -- their data IS these typed
records; see the parity gate.

Value policy: every Decimal -> float|None. Time-series rows are typed (date + value(s)); the `date`
is as-filed text -- real ISO dates in N-MFP3's daily series, synthetic "week_N"/"friday_N" labels
(or null) in the legacy N-MFP2 Friday-snapshot schema. N-MFP2 omits the registrant/series names
(-> null) that N-MFP3 carries; both schema versions feed these same models.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel

# --- time-series rows -------------------------------------------------------


class NmfpSeriesYield(WireModel):
    date: str | None
    gross_yield: float | None


class NmfpNavPoint(WireModel):
    date: str | None
    nav_per_share: float | None


class NmfpLiquidityPoint(WireModel):
    date: str | None
    daily_liquid_value: float | None
    weekly_liquid_value: float | None
    pct_daily_liquid: float | None
    pct_weekly_liquid: float | None


class NmfpClassFlow(WireModel):
    date: str | None
    gross_subscriptions: float | None
    gross_redemptions: float | None


class NmfpClassYield(WireModel):
    date: str | None
    net_yield: float | None


# --- general info / series / share class ------------------------------------


class NmfpGeneralInfo(WireModel):
    report_date: str | None
    registrant_name: str | None  # null on N-MFP2 (the legacy schema omits the registrant name)
    cik: str | None
    registrant_lei: str | None
    series_name: str | None  # null on N-MFP2
    series_lei: str | None
    series_id: str | None
    total_share_classes: int | None
    final_filing: bool


class NmfpSeriesLevelInfo(WireModel):
    fund_category: str | None
    avg_portfolio_maturity: int | None  # WAM, days
    avg_life_maturity: int | None  # WAL, days
    cash: float | None
    total_value_portfolio_securities: float | None
    amortized_cost_portfolio_securities: float | None
    total_value_other_assets: float | None
    total_value_liabilities: float | None
    net_assets: float | None
    shares_outstanding: float | None
    seek_stable_price: bool
    stable_price_per_share: float | None
    seven_day_gross_yields: list[NmfpSeriesYield]
    daily_nav_per_share: list[NmfpNavPoint]
    liquidity_details: list[NmfpLiquidityPoint]


class NmfpShareClassInfo(WireModel):
    class_name: str | None
    class_id: str | None
    min_initial_investment: float | None
    net_assets: float | None
    shares_outstanding: float | None
    daily_nav: list[NmfpNavPoint]
    daily_flows: list[NmfpClassFlow]
    seven_day_net_yields: list[NmfpClassYield]


# --- portfolio securities ---------------------------------------------------


class NmfpCreditRating(WireModel):
    agency: str | None
    rating: str | None


class NmfpCollateralIssuer(WireModel):
    issuer_name: str | None
    lei: str | None
    cusip: str | None
    maturity_date: str | None  # as-filed text
    coupon: float | None
    principal_amount: float | None
    collateral_value: float | None
    collateral_category: str | None


class NmfpRepurchaseAgreement(WireModel):
    open_flag: bool
    cleared_flag: bool
    tri_party_flag: bool
    collateral: list[NmfpCollateralIssuer]


class NmfpPortfolioSecurity(WireModel):
    issuer_name: str | None
    title: str | None
    cusip: str | None  # N-MFP2 falls back to otherUniqueId when CUSIP is absent
    isin: str | None
    lei: str | None
    cik: str | None  # raw issuer CIK as filed (not the envelope filer cik)
    investment_category: str | None
    maturity_date_wam: str | None  # as-filed text (all N-MFP maturities are raw, not parsed)
    maturity_date_wal: str | None
    final_maturity_date: str | None
    yield_rate: float | None
    market_value: float | None  # value INCLUDING any sponsor support
    amortized_cost: float | None  # value EXCLUDING any sponsor support
    pct_of_nav: float | None
    daily_liquid: bool
    weekly_liquid: bool
    illiquid: bool
    demand_feature: bool
    guarantee: bool
    enhancement: bool
    ratings: list[NmfpCreditRating]
    repo_agreement: NmfpRepurchaseAgreement | None


class NmfpData(WireModel):
    kind: Literal["nmfp"] = "nmfp"
    form: str | None
    cik: str | None
    name: str | None
    series_id: str | None
    report_date: str | None
    net_assets: float | None
    fund_category: str | None
    num_securities: int | None
    num_share_classes: int | None
    average_maturity_wam: int | None
    average_maturity_wal: int | None
    general_info: NmfpGeneralInfo | None
    series_info: NmfpSeriesLevelInfo | None
    share_classes: list[NmfpShareClassInfo]
    securities: list[NmfpPortfolioSecurity]
