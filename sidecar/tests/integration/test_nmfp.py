"""Integration (U57a): N-MFP2/N-MFP3 money market fund monthly report over one `MoneyMarketFund`
-> kind=nmfp.

N-MFP has ZERO XBRL -- edgar lxml-parses the submission XML into general info, a series-level block
(scalars + three time series), per-share-class blocks (each with three time series), and a flat
portfolio-securities list whose rows carry NRSRO ratings and an optional repurchase-agreement
sub-record with its own collateral list. Three fixtures pin the matrix:

  invesco_prime_v3  N-MFP3 Prime fund: real ISO-dated daily time series, multi-class, repos whose
                    collateral spans corporate debt; NO security-level ratings (Invesco files NRSRO
                    only on demand-feature/guarantee providers, which edgar does not surface) -> []
  legacy_v2         N-MFP2 (legacy schema): null registrant/series names, synthetic time-series date
                    labels ("week_1" / null), a security whose CUSIP falls back to otherUniqueId, and
                    repo collateral with a null CUSIP
  goldman_amend_v3  N-MFP3/A amendment (dispatch via the "/A" form): Government fund, 89 rated
                    securities; sec[0] is simultaneously rated, a repo, and carries collateral

Every Decimal crosses as float|None; all maturity/report dates are as-filed text (edgar parses none of
them). N-MFP2 omits the registrant/series names that N-MFP3 carries -> null.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_PRIME = "0001145549-25-016960"  # N-MFP3, Invesco Premier Portfolio (Prime, ISO time series, repos)
_LEGACY = "0001145549-23-015057"  # N-MFP2, legacy schema (null registrant/series, synthetic labels)
_GOLDMAN = "0001145549-25-018427"  # N-MFP3/A, Goldman FS Treasury Obligations (amendment + ratings)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _nmfp(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "MoneyMarketFund"  # every N-MFP2/N-MFP3 (+/A) -> this one object
    assert body["data"] is not None
    assert body["data"]["kind"] == "nmfp"
    return body


def test_nmfp_prime_v3_iso_timeseries_repos(client: TestClient, golden) -> None:
    body = _nmfp(client, _PRIME)
    data = body["data"]
    assert data["form"] == "N-MFP3"

    gi = data["general_info"]
    assert gi["registrant_name"] == "Invesco Treasurer's Series Trust"
    assert gi["series_name"] == "Invesco Premier Portfolio"
    assert gi["series_id"] == "S000000173"
    assert gi["cik"] == "0000828806"
    assert gi["report_date"] == "2025-02-28"  # as-filed text, not a parsed date
    assert gi["total_share_classes"] == 6
    assert gi["final_filing"] is False

    si = data["series_info"]
    assert si["fund_category"] == "Prime"
    assert si["avg_portfolio_maturity"] == 34  # WAM, days
    assert si["avg_life_maturity"] == 62  # WAL, days
    assert si["net_assets"] == 8665733413.82
    assert si["seek_stable_price"] is True
    assert si["stable_price_per_share"] == 1.0
    # N-MFP3 daily series: real ISO dates, one row per business day in the period
    assert len(si["seven_day_gross_yields"]) == 19
    assert si["seven_day_gross_yields"][0] == {"date": "2025-02-03", "gross_yield": 0.0459}
    assert len(si["daily_nav_per_share"]) == 19
    assert si["daily_nav_per_share"][0] == {"date": "2025-02-03", "nav_per_share": 1.0002}
    assert len(si["liquidity_details"]) == 19

    classes = data["share_classes"]
    assert len(classes) == 6
    investor = next(c for c in classes if c["class_name"] == "Investor")
    assert investor["class_id"] == "C000000397"
    assert investor["net_assets"] == 229400091.69
    assert investor["shares_outstanding"] == 229387902.957
    assert len(investor["daily_nav"]) == 19
    assert len(investor["daily_flows"]) == 19
    assert len(investor["seven_day_net_yields"]) == 19

    secs = data["securities"]
    assert len(secs) == 120
    # Invesco files NRSRO ratings only on demand-feature/guarantee providers; edgar surfaces the
    # security-level assigningNRSRORating only, which Invesco omits -> every row's ratings is []
    assert all(s["ratings"] == [] for s in secs)
    cp = next(s for s in secs if s["issuer_name"] == "ABS Bank Ltd.")
    assert cp["investment_category"] == "Financial Company Commercial Paper"
    assert cp["cusip"] == "0020NABG4"
    assert cp["market_value"] == 50002757.5
    assert cp["amortized_cost"] == 50002757.5
    assert cp["pct_of_nav"] == 0.0058
    assert cp["yield_rate"] == 0.0442
    assert cp["repo_agreement"] is None

    repo_sec = next(s for s in secs if s["repo_agreement"] is not None)
    assert repo_sec["issuer_name"] == "J.P. Morgan Securities LLC"
    ra = repo_sec["repo_agreement"]
    assert ra["open_flag"] is True
    assert ra["cleared_flag"] is False
    assert ra["tri_party_flag"] is True
    assert len(ra["collateral"]) == 57
    coll0 = ra["collateral"][0]
    assert coll0["issuer_name"] == "ACCELERATE360 HOLDINGS LLC     SR SEC GLBL 31"  # as-filed spacing
    assert coll0["cusip"] == "00456LAC6"
    assert coll0["coupon"] == 11.0
    assert coll0["principal_amount"] == 35715840.0
    assert coll0["collateral_value"] == 37170268.37
    assert coll0["collateral_category"] == "Corporate Debt Securities"

    golden("filing", "nmfp_invesco_prime", body)


def test_nmfp_legacy_v2_synthetic_labels(client: TestClient, golden) -> None:
    body = _nmfp(client, _LEGACY)
    data = body["data"]
    assert data["form"] == "N-MFP2"

    gi = data["general_info"]
    # N-MFP2 legacy schema omits the registrant + series names that N-MFP3 carries
    assert gi["registrant_name"] is None
    assert gi["series_name"] is None
    assert gi["series_id"] == "S000011990"
    assert gi["cik"] == "0000862021"
    assert gi["report_date"] == "2023-02-28"
    assert gi["total_share_classes"] == 11

    si = data["series_info"]
    assert si["fund_category"] == "Exempt Government"
    assert si["net_assets"] == 13654510527.28
    # legacy schema: Friday weekly snapshots with synthetic date labels (or null), not ISO dates
    assert si["seven_day_gross_yields"] == [{"date": None, "gross_yield": 0.0451}]
    assert si["daily_nav_per_share"][0] == {"date": "week_1", "nav_per_share": 1.0}

    classes = data["share_classes"]
    assert len(classes) == 11
    # the legacy schema files no class names -> null; class ids still present
    assert classes[0]["class_name"] is None
    assert classes[0]["class_id"] == "C000032709"
    assert classes[0]["net_assets"] == 5648001151.76

    secs = data["securities"]
    assert len(secs) == 67
    boa = secs[0]
    assert boa["issuer_name"] == "Bank of America"
    # no CUSIP filed -> edgar falls back to the otherUniqueId (CUSIP_coupon_maturity synthetic id)
    assert boa["cusip"] == "03199J004_4.55_0301"
    assert boa["market_value"] == 90000000.0
    assert boa["daily_liquid"] is True
    assert boa["weekly_liquid"] is True
    ra = boa["repo_agreement"]
    assert ra is not None
    assert ra["open_flag"] is False
    assert ra["tri_party_flag"] is False
    assert len(ra["collateral"]) == 1
    coll = ra["collateral"][0]
    assert coll["issuer_name"] == "U.S. Treasury Note"
    assert coll["cusip"] is None  # collateral CUSIP absent in the legacy filing -> null
    assert coll["coupon"] == 2.625
    assert coll["collateral_value"] == 91800085.85

    golden("filing", "nmfp_legacy_v2", body)


def test_nmfp_amendment_with_ratings(client: TestClient, golden) -> None:
    body = _nmfp(client, _GOLDMAN)
    data = body["data"]
    assert data["form"] == "N-MFP3/A"  # amendment dispatches through MONEY_MARKET_FORMS

    gi = data["general_info"]
    assert gi["registrant_name"] == "Goldman Sachs Trust"
    assert gi["series_name"] == "Goldman Sachs Financial Square Fund - Treasury Obligations"
    assert gi["series_id"] == "S000009260"
    assert gi["cik"] == "0000822977"
    assert gi["report_date"] == "2024-09-30"
    assert gi["total_share_classes"] == 9

    si = data["series_info"]
    assert si["fund_category"] == "Government"
    assert si["avg_portfolio_maturity"] == 43
    assert si["avg_life_maturity"] == 91
    assert si["net_assets"] == 39930921078.01

    classes = data["share_classes"]
    assert len(classes) == 9
    inst = next(c for c in classes if c["class_name"] == "Institutional Shares")
    assert inst["class_id"] == "C000025302"
    assert inst["min_initial_investment"] == 10000000.0
    assert inst["net_assets"] == 33534706970.1

    secs = data["securities"]
    assert len(secs) == 93
    # Goldman files security-level NRSRO ratings: 89 of 93 rows carry an assigningNRSRORating
    assert sum(1 for s in secs if s["ratings"]) == 89

    sec0 = secs[0]  # simultaneously rated, a repo, and carrying collateral
    assert sec0["issuer_name"] == "PRUDENTIAL INSURANCE COMPANY OF AMERICA (THE)"
    assert sec0["cusip"] == "502362784"
    assert sec0["lei"] == "X574KRZ6V5A7UBU45C31"
    assert sec0["cik"] == "0000729057"  # issuer's own CIK as filed (not the envelope filer cik)
    assert sec0["maturity_date_wam"] == "2024-10-01"  # as-filed text
    assert sec0["yield_rate"] == 0.0488
    assert sec0["market_value"] == 22062500.0
    assert sec0["pct_of_nav"] == 0.0006
    assert sec0["ratings"] == [
        {"agency": "Fitch, Inc.", "rating": "F1+"},
        {"agency": "Standard and Poor's Ratings Services", "rating": "A-1+"},
    ]
    ra = sec0["repo_agreement"]
    assert ra is not None
    assert len(ra["collateral"]) == 1
    coll = ra["collateral"][0]
    assert coll["issuer_name"] == "UNITED STATES DEPARTMENT OF THE TREASURY"
    assert coll["cusip"] == "912803EE9"
    assert coll["maturity_date"] == "2043-11-15"
    assert coll["collateral_value"] == 22503750.0
    assert coll["collateral_category"] == "U.S. Treasuries (including strips)"

    golden("filing", "nmfp_goldman_amend", body)
