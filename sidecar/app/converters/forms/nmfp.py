"""U57a converter: edgar.funds.nmfp3.MoneyMarketFund -> NmfpData, explicit field-by-field.

Reads only the four stored structures (general_info, series_info, share_classes, securities). The
DataFrame-view methods and the derived scalar properties are never touched -- their data IS these
typed records. Series/class time series are stored as list[dict] with fixed keys (consistent across
the N-MFP2 and N-MFP3 schemas); each row maps to a typed point model -- explicit key reads, never a
vars()/getattr loop.
"""

from __future__ import annotations

from edgar.funds.nmfp3 import (
    CollateralIssuer,
    CreditRating,
    GeneralInfo,
    MoneyMarketFund,
    PortfolioSecurity,
    RepurchaseAgreement,
    SeriesLevelInfo,
    ShareClassInfo,
)

from app.cik import pad_cik
from app.models.forms.nmfp import (
    NmfpClassFlow,
    NmfpClassYield,
    NmfpCollateralIssuer,
    NmfpCreditRating,
    NmfpData,
    NmfpGeneralInfo,
    NmfpLiquidityPoint,
    NmfpNavPoint,
    NmfpPortfolioSecurity,
    NmfpRepurchaseAgreement,
    NmfpSeriesLevelInfo,
    NmfpSeriesYield,
    NmfpShareClassInfo,
)
from app.serialize import to_float, to_int, to_str

# --- general info -----------------------------------------------------------


def _general_info(g: GeneralInfo) -> NmfpGeneralInfo:
    cik = to_str(g.cik)
    return NmfpGeneralInfo(
        report_date=to_str(g.report_date),
        registrant_name=to_str(g.registrant_name),
        cik=pad_cik(cik) if cik else None,
        registrant_lei=to_str(g.registrant_lei),
        series_name=to_str(g.series_name),
        series_lei=to_str(g.series_lei),
        series_id=to_str(g.series_id),
        total_share_classes=to_int(g.total_share_classes),
        final_filing=g.final_filing,
    )


# --- series-level info + time series ----------------------------------------


def _series_yield(d: dict) -> NmfpSeriesYield:
    return NmfpSeriesYield(date=to_str(d["date"]), gross_yield=to_float(d["gross_yield"]))


def _nav_point(d: dict) -> NmfpNavPoint:
    return NmfpNavPoint(date=to_str(d["date"]), nav_per_share=to_float(d["nav_per_share"]))


def _liquidity_point(d: dict) -> NmfpLiquidityPoint:
    return NmfpLiquidityPoint(
        date=to_str(d["date"]),
        daily_liquid_value=to_float(d["daily_liquid_value"]),
        weekly_liquid_value=to_float(d["weekly_liquid_value"]),
        pct_daily_liquid=to_float(d["pct_daily_liquid"]),
        pct_weekly_liquid=to_float(d["pct_weekly_liquid"]),
    )


def _series_info(s: SeriesLevelInfo) -> NmfpSeriesLevelInfo:
    return NmfpSeriesLevelInfo(
        fund_category=to_str(s.fund_category),
        avg_portfolio_maturity=to_int(s.avg_portfolio_maturity),
        avg_life_maturity=to_int(s.avg_life_maturity),
        cash=to_float(s.cash),
        total_value_portfolio_securities=to_float(s.total_value_portfolio_securities),
        amortized_cost_portfolio_securities=to_float(s.amortized_cost_portfolio_securities),
        total_value_other_assets=to_float(s.total_value_other_assets),
        total_value_liabilities=to_float(s.total_value_liabilities),
        net_assets=to_float(s.net_assets),
        shares_outstanding=to_float(s.shares_outstanding),
        seek_stable_price=s.seek_stable_price,
        stable_price_per_share=to_float(s.stable_price_per_share),
        seven_day_gross_yields=[_series_yield(d) for d in s.seven_day_gross_yields],
        daily_nav_per_share=[_nav_point(d) for d in s.daily_nav_per_share],
        liquidity_details=[_liquidity_point(d) for d in s.liquidity_details],
    )


# --- share classes + time series --------------------------------------------


def _class_flow(d: dict) -> NmfpClassFlow:
    return NmfpClassFlow(
        date=to_str(d["date"]),
        gross_subscriptions=to_float(d["gross_subscriptions"]),
        gross_redemptions=to_float(d["gross_redemptions"]),
    )


def _class_yield(d: dict) -> NmfpClassYield:
    return NmfpClassYield(date=to_str(d["date"]), net_yield=to_float(d["net_yield"]))


def _share_class(sc: ShareClassInfo) -> NmfpShareClassInfo:
    return NmfpShareClassInfo(
        class_name=to_str(sc.class_name),
        class_id=to_str(sc.class_id),
        min_initial_investment=to_float(sc.min_initial_investment),
        net_assets=to_float(sc.net_assets),
        shares_outstanding=to_float(sc.shares_outstanding),
        daily_nav=[_nav_point(d) for d in sc.daily_nav],
        daily_flows=[_class_flow(d) for d in sc.daily_flows],
        seven_day_net_yields=[_class_yield(d) for d in sc.seven_day_net_yields],
    )


# --- portfolio securities ---------------------------------------------------


def _rating(r: CreditRating) -> NmfpCreditRating:
    return NmfpCreditRating(agency=to_str(r.agency), rating=to_str(r.rating))


def _collateral(c: CollateralIssuer) -> NmfpCollateralIssuer:
    return NmfpCollateralIssuer(
        issuer_name=to_str(c.issuer_name),
        lei=to_str(c.lei),
        cusip=to_str(c.cusip),
        maturity_date=to_str(c.maturity_date),
        coupon=to_float(c.coupon),
        principal_amount=to_float(c.principal_amount),
        collateral_value=to_float(c.collateral_value),
        collateral_category=to_str(c.collateral_category),
    )


def _repo(r: RepurchaseAgreement | None) -> NmfpRepurchaseAgreement | None:
    if r is None:
        return None
    return NmfpRepurchaseAgreement(
        open_flag=r.open_flag,
        cleared_flag=r.cleared_flag,
        tri_party_flag=r.tri_party_flag,
        collateral=[_collateral(c) for c in r.collateral],
    )


def _security(s: PortfolioSecurity) -> NmfpPortfolioSecurity:
    return NmfpPortfolioSecurity(
        issuer_name=to_str(s.issuer_name),
        title=to_str(s.title),
        cusip=to_str(s.cusip),
        isin=to_str(s.isin),
        lei=to_str(s.lei),
        cik=to_str(s.cik),
        investment_category=to_str(s.investment_category),
        maturity_date_wam=to_str(s.maturity_date_wam),
        maturity_date_wal=to_str(s.maturity_date_wal),
        final_maturity_date=to_str(s.final_maturity_date),
        yield_rate=to_float(s.yield_rate),
        market_value=to_float(s.market_value),
        amortized_cost=to_float(s.amortized_cost),
        pct_of_nav=to_float(s.pct_of_nav),
        daily_liquid=s.daily_liquid,
        weekly_liquid=s.weekly_liquid,
        illiquid=s.illiquid,
        demand_feature=s.demand_feature,
        guarantee=s.guarantee,
        enhancement=s.enhancement,
        ratings=[_rating(r) for r in s.ratings],
        repo_agreement=_repo(s.repo_agreement),
    )


def nmfp_data(obj: MoneyMarketFund) -> NmfpData:
    filing = obj.filing
    cik = to_str(obj.cik)
    return NmfpData(
        form=to_str(filing.form) if filing is not None else None,
        cik=pad_cik(cik) if cik else None,
        name=to_str(obj.name),
        series_id=to_str(obj.series_id),
        report_date=to_str(obj.report_date),
        net_assets=to_float(obj.net_assets),
        fund_category=to_str(obj.fund_category),
        num_securities=obj.num_securities,
        num_share_classes=obj.num_share_classes,
        average_maturity_wam=to_int(obj.average_maturity_wam),
        average_maturity_wal=to_int(obj.average_maturity_wal),
        general_info=_general_info(obj.general_info),
        series_info=_series_info(obj.series_info),
        share_classes=[_share_class(sc) for sc in obj.share_classes],
        securities=[_security(s) for s in obj.securities],
    )
