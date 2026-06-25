"""Integration (U55b): the 497K fund summary prospectus over one `Prospectus497K` -> kind=prospectus_497k.

497K has ZERO XBRL -- edgar HTML-parses fund identity, per-share-class fees + the $10K expense example,
and the average-annual-returns table. Five fixtures pin the matrix:

  vanguard_caltax      2 classes, full performance (best AND worst quarter, both dated), clean fees
  allspring_emgrowth   4 classes, 12b1 + fee waiver, worst-quarter-only with an EMPTY date (-> null)
  allspring_ultrashort 1 class WITH a front-end sales load, waiver, acquired-fund fees, performance
  netlease_etf         1-class ETF, performance present but NO best/worst quarter
  reckoner_clo         new 1-class ETF: NO performance history (empty list), null quarters, partial expenses

Parsed Decimal fees/returns cross as floats (the U53a rule); the $10K expense-example dollars as ints.
edgar's metadata extractor does not surface prospectus_date / portfolio_managers for these filings, so
those are faithfully null / empty on the wire. inception_date is structurally null (edgar's from_filing
never sets it) but is still carried from the typed backing list, not the lossy `performance` DataFrame.

497K/A (amendment): zero recent filings in SEC EFTS as of 2026-06; the matches_form expansion is
validated by other form families' /A amendment tests (N-CEN/A, N-MFP3/A, S-3/A).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_VANGUARD = "0001683863-25-002784"  # 497K, Vanguard CA Long-Term Tax-Exempt (2 classes, best+worst quarter)
_EMGROWTH = "0001081400-25-000275"  # 497K, Allspring Emerging Growth (4 classes, 12b1 + waiver, worst-only)
_ULTRASHORT = "0001081400-25-000273"  # 497K, Allspring Ultra Short-Term Income (1 class, sales load)
_NETLEASE = "0000894189-25-004849"  # 497K, NetLease Corporate Real Estate ETF (perf, no quarters)
_RECKONER = "0000894189-25-004840"  # 497K, Reckoner Leveraged AAA CLO ETF (no performance)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _p497k(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Prospectus497K"  # every 497K (+/A) -> this one object
    assert body["data"] is not None
    assert body["data"]["kind"] == "prospectus_497k"
    return body


def test_497k_multiclass_full_performance(client: TestClient, golden) -> None:
    body = _p497k(client, _VANGUARD)
    data = body["data"]
    assert data["form"] == "497K"
    assert data["fund_name"] == "Vanguard California Long-Term Tax-Exempt Fund"
    assert data["series_id"] == "S000002567"
    assert data["prospectus_date"] is None  # edgar metadata extractor finds none for this filing
    assert data["portfolio_managers"] == []
    assert data["portfolio_turnover"] == 81.0
    # two share classes; tickers are the derived view's source (parity excludes the derived list)
    classes = data["share_classes"]
    assert [c["ticker"] for c in classes] == ["VCITX", "VCLAX"]
    investor = classes[0]
    assert investor["class_name"] == "Investor Shares"
    assert investor["class_id"] == "C000007068"
    assert investor["management_fee"] == 0.13
    assert investor["other_expenses"] == 0.01
    assert investor["total_annual_expenses"] == 0.14
    assert investor["twelve_b1_fee"] is None
    assert investor["expense_1yr"] == 14
    assert investor["expense_10yr"] == 179
    assert classes[1]["total_annual_expenses"] == 0.09
    # best AND worst quarter, both with as-filed dates
    assert data["best_quarter"] == {"return_pct": 8.8, "date": "December 31, 2023"}
    assert data["worst_quarter"] == {"return_pct": -6.78, "date": "March 31, 2022"}
    perf = data["performance_returns"]
    assert len(perf) == 6
    assert perf[0]["label"] == "Return Before Taxes"
    assert perf[0]["section"] == "Vanguard California Long-Term Tax-Exempt Fund Investor Shares"
    assert perf[0]["return_1yr"] == 2.09
    assert perf[0]["return_10yr"] == 2.61
    assert perf[0]["inception_date"] is None
    golden("filing", "prospectus_497k_vanguard_caltax", body)


def test_497k_four_classes_waiver_empty_quarter_date(client: TestClient, golden) -> None:
    body = _p497k(client, _EMGROWTH)
    data = body["data"]
    assert data["form"] == "497K"
    assert data["fund_name"] == "Allspring Emerging Growth Fund"
    assert data["series_id"] == "S000015703"
    assert data["portfolio_turnover"] == 79.0
    classes = data["share_classes"]
    assert len(classes) == 4
    assert [c["ticker"] for c in classes] == ["WEMAX", "WEMCX", "WEGRX", "WEMIX"]
    class_a = classes[0]
    assert class_a["class_name"] == "Class A"
    assert class_a["management_fee"] == 0.85
    assert class_a["twelve_b1_fee"] == 0.0  # 0.00 is a real parsed value, not absent
    assert class_a["total_annual_expenses"] == 1.40
    assert class_a["fee_waiver"] == 1.22
    # worst quarter only; its date is an empty cell -> null (to_str drops "")
    assert data["best_quarter"] is None
    assert data["worst_quarter"] == {"return_pct": -25.02, "date": None}
    assert len(data["performance_returns"]) == 19
    golden("filing", "prospectus_497k_allspring_emgrowth", body)


def test_497k_single_class_sales_load(client: TestClient, golden) -> None:
    body = _p497k(client, _ULTRASHORT)
    data = body["data"]
    assert data["fund_name"] == "Allspring Ultra Short-Term Income Fund"
    assert data["series_id"] == "S000007431"
    assert data["portfolio_turnover"] == 48.0
    classes = data["share_classes"]
    assert len(classes) == 1
    sc = classes[0]
    assert sc["class_name"] == "Class A"
    assert sc["ticker"] == "SADAX"
    assert sc["max_sales_load"] == 2.00  # front-end load present on this class
    assert sc["acquired_fund_fees"] == 0.01
    assert sc["total_annual_expenses"] == 0.69
    assert sc["fee_waiver"] == 0.51
    assert sc["expense_1yr"] == 251
    assert sc["expense_10yr"] == 1007
    assert data["best_quarter"] is None
    assert data["worst_quarter"] == {"return_pct": -2.32, "date": None}
    assert len(data["performance_returns"]) == 9
    golden("filing", "prospectus_497k_allspring_ultrashort", body)


def test_497k_etf_performance_no_quarters(client: TestClient, golden) -> None:
    body = _p497k(client, _NETLEASE)
    data = body["data"]
    assert data["fund_name"] == "NetLease Corporate Real Estate ETF"
    assert data["series_id"] == "S000065033"
    assert data["portfolio_turnover"] == 15.0
    classes = data["share_classes"]
    assert len(classes) == 1
    sc = classes[0]
    assert sc["ticker"] == "NETL"
    assert sc["management_fee"] == 0.60
    assert sc["total_annual_expenses"] == 0.60
    assert sc["expense_10yr"] == 750
    # performance present, but no best/worst quarter parsed
    assert data["best_quarter"] is None
    assert data["worst_quarter"] is None
    perf = data["performance_returns"]
    assert len(perf) == 6
    assert perf[0]["label"] == "Return Before Taxes"
    assert perf[0]["return_1yr"] == -1.12
    assert perf[0]["return_10yr"] is None
    assert perf[0]["return_since_inception"] == 3.40
    golden("filing", "prospectus_497k_netlease_etf", body)


def test_497k_new_etf_no_performance(client: TestClient, golden) -> None:
    body = _p497k(client, _RECKONER)
    data = body["data"]
    assert data["fund_name"] == "Reckoner Leveraged AAA CLO ETF"
    assert data["series_id"] == "S000093690"
    assert data["portfolio_turnover"] == 80.0
    classes = data["share_classes"]
    assert len(classes) == 1
    sc = classes[0]
    assert sc["ticker"] == "RAAA"
    assert sc["management_fee"] == 0.30
    assert sc["twelve_b1_fee"] == 0.0
    assert sc["total_annual_expenses"] == 0.30
    assert sc["expense_1yr"] == 31
    assert sc["expense_3yr"] == 97
    assert sc["expense_5yr"] is None  # new fund: only 1yr/3yr expense-example columns
    assert sc["expense_10yr"] is None
    # brand-new fund: no return history, no best/worst quarter
    assert data["performance_returns"] == []
    assert data["best_quarter"] is None
    assert data["worst_quarter"] is None
    golden("filing", "prospectus_497k_reckoner_clo", body)
