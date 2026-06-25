"""Integration (U56): the NPORT-P/EX fund portfolio report over one `FundReport` -> kind=nport.

NPORT has ZERO XBRL -- edgar lxml-parses the submission XML into a header tree, general/fund info
(risk metrics, monthly returns + flows) and a flat holdings list whose derivative rows carry a typed
forward/swap/future/option/swaption sub-record. Five fixtures pin the matrix:

  1ws_credit    single-series fund (NO seriesClassInfo -> null), 3 FX risk-metric currencies, a
                floating-rate foreign bond (debt_security, conditional currency + exchange rate), a
                receive-fixed SWP and a short FUT; literal "N/A" name/cusip rows pass through as-filed
  oshaughnessy  minimal single-class equity fund: no metrics, no derivatives, one clean US equity
  sands_global  multi-class equity + an EUR/USD FX FWD (forward_derivative leg)
  acadian_em    643-holding EM fund: foreign equity priced in IDR (conditional currency), a PLN FWD,
                and a WAR whose data edgar files into option_derivative (delta "XXXX" sentinel kept)
  pimco         large multi-series fund: swaption (SWO) derivatives with nested swap sub-records

Parsed Decimals cross as floats; DebtSecurity.maturity_date (the one edgar parses) crosses as an ISO
date; every other date stays as-filed text. The decimal_or_na "N/A" no-number sentinel -> null; a filed
empty string (e.g. an unclassed return's class_id) -> null via to_str. ccc is masked "XXXXXXXX".
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_1WS = "0001752724-25-076577"  # NPORT-P, 1WS Credit Income Fund (bond + SWP + FUT + FX risk metrics)
_OSHAUGHNESSY = "0001145549-25-021726"  # NPORT-P, O'Shaughnessy Market Leaders Value (simple equity)
_SANDS = "0001752724-25-075388"  # NPORT-P, Sands Capital Global Growth (equity + FX forward)
_ACADIAN = "0001752724-25-075368"  # NPORT-P, Acadian Emerging Markets (warrant-as-option + EM foreign)
_PIMCO = "0001099263-26-007248"  # NPORT-P, PIMCO Funds (swaption derivative, nested swap)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _nport(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "FundReport"  # every NPORT-P/EX (+ N-PORT/A) -> this one object
    assert body["data"] is not None
    assert body["data"]["kind"] == "nport"
    return body


def _first_deriv(invs: list[dict], leg: str) -> dict:
    return next(i for i in invs if i["derivative_info"] and i["derivative_info"][leg] is not None)


def test_nport_credit_bonds_swaps_futures(client: TestClient, golden) -> None:
    body = _nport(client, _1WS)
    data = body["data"]
    assert data["form"] == "NPORT-P"

    gi = data["general_info"]
    assert gi["name"] == "1WS CREDIT INCOME FUND"
    assert gi["series_name"] == "1WS Credit Income Fund"
    assert gi["series_id"] is None  # single-series fund: no series in genInfo
    assert gi["cik"] == "0001748680"
    assert gi["rep_period_date"] == "2025-01-31"  # as-filed text, not a parsed date
    assert gi["fiscal_year_end"] == "2025-10-31"
    assert gi["is_final_filing"] is False
    assert gi["reg_lei"] == "549300B58HSKB8RHUQ19"

    hdr = data["header"]
    assert hdr["submission_type"] == "NPORT-P"
    assert hdr["is_confidential"] is False
    assert hdr["filer_info"]["series_class_info"] is None  # single-series: seriesClassInfo absent
    assert hdr["filer_info"]["issuer_credentials"]["ccc"] == "XXXXXXXX"  # masked in public filings

    fi = data["fund_info"]
    assert fi["total_assets"] == 588661556.99
    assert fi["total_liabilities"] == 76539489.38
    assert fi["net_assets"] == 512122067.61
    assert fi["is_non_cash_collateral"] is False
    assert sorted(fi["current_metrics"]) == ["AUD", "EUR", "USD"]
    aud = fi["current_metrics"]["AUD"]
    assert aud["interest_rate_risk_dv01"]["period_1yr"] == 14.505552
    assert aud["interest_rate_risk_dv100"]["period_1yr"] == 1450.555204
    assert fi["credit_spread_risk_investment_grade"]["period_1yr"] == 1470.825355
    ri = fi["return_info"]
    assert len(ri["monthly_total_returns"]) == 2
    assert ri["monthly_total_returns"][0]["class_id"] is None  # filed empty -> to_str("") = None
    assert ri["monthly_total_returns"][0]["return_month1"] == 0.72
    assert ri["realized_change_month1"]["net_realized_gain"] == 926817.78
    assert fi["monthly_flow1"]["sales"] == 32694126.8
    assert fi["monthly_flow1"]["redemption"] == 0.0

    invs = data["investments"]
    assert len(invs) == 607
    # a short position files name/cusip as the literal "N/A" sentinel -- passed through, not nulled
    assert any(i["name"] == "N/A" for i in invs)

    debt = next(i for i in invs if i["debt_security"] is not None)
    assert debt["name"] == "Vasco Finance"
    assert debt["cusip"] == "BCC3HJWV1"
    assert debt["identifiers"]["isin"] == "PTTGCFOM0028"
    assert debt["balance"] == 900000.0
    assert debt["units"] == "PA"  # principal amount
    assert debt["currency_conditional_code"] == "EUR"  # denomination != reporting currency
    assert debt["exchange_rate"] == 0.96395
    assert debt["value_usd"] == 947569.89
    assert debt["payoff_profile"] == "Long"
    assert debt["asset_category"] == "ABS-O"
    assert debt["investment_country"] == "PT"
    assert debt["fair_value_level"] == "2"
    ds = debt["debt_security"]
    assert ds["maturity_date"] == "2042-10-27"  # edgar-parsed datetime -> ISO date
    assert ds["coupon_kind"] == "Floating"
    assert ds["annualized_rate"] == 8.405
    assert ds["is_default"] is False
    assert ds["are_payments_in_arrears"] is False

    swap = _first_deriv(invs, "swap_derivative")
    assert swap["value_usd"] == -454765.54  # negative leg value for the derivative
    assert swap["payoff_profile"] == "N/A"  # literal sentinel preserved on derivatives
    assert swap["derivative_info"]["derivative_category"] == "SWP"
    sd = swap["derivative_info"]["swap_derivative"]
    assert sd["counterparty_name"] == "Morgan Stanley"
    assert sd["notional_amount"] == -2000000.0
    assert sd["currency"] == "USD"
    assert sd["unrealized_appreciation"] == 365234.46
    assert sd["termination_date"] == "2064-11-18"  # as-filed text
    assert sd["fixed_rate_receive"] == 5.0

    fut = _first_deriv(invs, "future_derivative")
    assert fut["identifiers"]["ticker"] == "ADH5"
    assert fut["balance"] == -75.0  # short contracts
    assert fut["derivative_info"]["derivative_category"] == "FUT"
    fd = fut["derivative_info"]["future_derivative"]
    assert fd["counterparty_name"] == "Wells Fargo Securities, LLC"
    assert fd["payoff_profile"] == "Short"
    assert fd["expiration_date"] == "2025-03-17"
    assert fd["notional_amount"] == -4662375.0
    assert fd["unrealized_appreciation"] == 106313.0
    assert fd["reference_entity_name"] == "AUDUSD Crncy Fut  Mar25"

    golden("filing", "nport_1ws_credit", body)


def test_nport_simple_equity(client: TestClient, golden) -> None:
    body = _nport(client, _OSHAUGHNESSY)
    data = body["data"]
    assert data["form"] == "NPORT-P"

    gi = data["general_info"]
    assert gi["name"] == "Advisors Series Trust"  # the trust, not the series
    assert gi["series_name"] == "O'Shaughnessy Market Leaders Value Fund"
    assert gi["series_id"] == "S000052915"
    assert gi["cik"] == "0001027596"
    assert gi["fiscal_year_end"] == "2025-07-31"

    sci = data["header"]["filer_info"]["series_class_info"]
    assert sci == {"series_id": "S000052915", "class_id": "C000166455"}

    fi = data["fund_info"]
    assert fi["total_assets"] == 222172462.31
    assert fi["net_assets"] == 222030048.92
    assert fi["current_metrics"] == {}  # equity fund: no interest-rate risk metrics
    assert fi["credit_spread_risk_investment_grade"] is None
    ri = fi["return_info"]
    assert len(ri["monthly_total_returns"]) == 1
    assert ri["monthly_total_returns"][0] == {
        "class_id": "C000166455",
        "return_month1": 10.83,
        "return_month2": -7.97,
        "return_month3": 4.89,
    }

    invs = data["investments"]
    assert len(invs) == 61
    eq = next(i for i in invs if i["name"] == "Lockheed Martin Corp")
    assert eq["cusip"] == "539830109"
    assert eq["identifiers"]["ticker"] == "LMT"
    assert eq["identifiers"]["isin"] == "US5398301094"
    assert eq["balance"] == 14540.0
    assert eq["units"] == "NS"  # number of shares
    assert eq["value_usd"] == 6731293.0
    assert eq["payoff_profile"] == "Long"
    assert eq["asset_category"] == "EC"
    assert eq["issuer_category"] == "CORP"
    assert eq["fair_value_level"] == "1"
    assert eq["debt_security"] is None
    assert eq["derivative_info"] is None

    golden("filing", "nport_oshaughnessy_equity", body)


def test_nport_forward_derivative(client: TestClient, golden) -> None:
    body = _nport(client, _SANDS)
    data = body["data"]

    gi = data["general_info"]
    assert gi["name"] == "ADVISORS' INNER CIRCLE FUND"
    assert gi["series_name"] == "Sands Capital Global Growth Fund"
    assert gi["series_id"] == "S000028356"
    assert gi["cik"] == "0000878719"

    fi = data["fund_info"]
    assert fi["total_assets"] == 1374798092.05
    assert fi["net_assets"] == 1256270085.88

    invs = data["investments"]
    assert len(invs) == 56
    fwd = _first_deriv(invs, "forward_derivative")
    assert fwd["name"] == "BROWN BROTHERS HARRIMAN & CO."
    assert fwd["value_usd"] == 989.7
    assert fwd["derivative_info"]["derivative_category"] == "FWD"
    leg = fwd["derivative_info"]["forward_derivative"]
    assert leg["counterparty_name"] == "BROWN BROTHERS HARRIMAN & CO."
    assert leg["amount_sold"] == 241873.99
    assert leg["currency_sold"] == "EUR"
    assert leg["amount_purchased"] == 251909.34
    assert leg["currency_purchased"] == "USD"
    assert leg["settlement_date"] == "2025-02-03"
    assert leg["unrealized_appreciation"] == 989.7

    golden("filing", "nport_sands_forward", body)


def test_nport_warrant_as_option_em_foreign(client: TestClient, golden) -> None:
    body = _nport(client, _ACADIAN)
    data = body["data"]

    gi = data["general_info"]
    assert gi["series_name"] == "Acadian Emerging Markets Portfolio"
    assert gi["series_id"] == "S000005712"
    assert gi["cik"] == "0000878719"

    invs = data["investments"]
    assert len(invs) == 643
    # EM equity denominated in a foreign currency: conditional code + the applied exchange rate
    em = next(i for i in invs if i["name"] == "PT ABM Investama Tbk")
    assert em["cusip"] == "N/A"  # no CUSIP for this foreign name -> literal sentinel as-filed
    assert em["identifiers"]["isin"] == "ID1000121502"
    assert em["balance"] == 68965.0
    assert em["currency_code"] is None
    assert em["currency_conditional_code"] == "IDR"
    assert em["exchange_rate"] == 16300.0
    assert em["value_usd"] == 14426.96
    assert em["investment_country"] == "ID"

    fwd = _first_deriv(invs, "forward_derivative")
    assert fwd["name"] == "BROWN BROTHERS"
    leg = fwd["derivative_info"]["forward_derivative"]
    assert leg["currency_sold"] == "PLN"
    assert leg["amount_sold"] == 156843.39
    assert leg["unrealized_appreciation"] == 344.52

    # a warrant: edgar files the row under derivative_category WAR but its data lands in option_derivative
    war = next(i for i in invs if i["derivative_info"] and i["derivative_info"]["derivative_category"] == "WAR")
    assert war["name"] == "SUCCESSMORE BEING PCL-NVDR WARRANT"
    assert war["currency_conditional_code"] == "THB"
    assert war["exchange_rate"] == 33.675
    assert war["value_usd"] == 0.0
    assert war["asset_category"] == "DE"
    opt = war["derivative_info"]["option_derivative"]
    assert opt is not None
    assert opt["put_or_call"] == "Call"
    assert opt["written_or_purchased"] == "Purchased"
    assert opt["share_number"] == 400.0
    assert opt["exercise_price"] == 2.0
    assert opt["exercise_price_currency"] == "THB"
    assert opt["expiration_date"] == "2025-05-28"
    assert opt["delta"] == "XXXX"  # non-numeric delta sentinel kept as raw filed text

    golden("filing", "nport_acadian_warrant", body)


def test_nport_swaption_derivative(client: TestClient, golden) -> None:
    body = _nport(client, _PIMCO)
    data = body["data"]
    assert data["form"] == "NPORT-P"

    gi = data["general_info"]
    assert gi["cik"] == "0000810893"  # the trust CIK, not the filer CIK

    invs = data["investments"]
    # PIMCO files swaptions (SWO) with nested swap sub-records
    swo_holdings = [i for i in invs if i["derivative_info"] and i["derivative_info"]["derivative_category"] == "SWO"]
    assert len(swo_holdings) >= 1

    swo = swo_holdings[0]
    assert swo["derivative_info"]["swaption_derivative"] is not None
    sd = swo["derivative_info"]["swaption_derivative"]
    assert sd["put_or_call"] == "Call"
    assert sd["written_or_purchased"] == "Purchased"
    assert sd["exercise_price"] == 2.17
    assert sd["exercise_price_currency"] == "USD"
    assert sd["expiration_date"] == "2032-07-19"
    assert sd["delta"] == "XXXX"  # non-numeric sentinel kept as raw filed text
    # swaption wraps a nested swap with its own counterparty and terms
    ns = sd["nested_swap"]
    assert ns is not None
    assert ns["counterparty_name"] == "MORGAN STANLEY & CO. LLC"
    assert ns["currency"] == "USD"

    golden("filing", "nport_pimco_swaption", body)
