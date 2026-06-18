"""Integration: /filing/{accession} envelope with typed ProxyStatement `data` (P4, kind=proxy).

One `ProxyStatement` backs DEF 14A and every 14A variant -> one kind (`proxy`); `form` is the
variant. `data` carries two legs: the XBRL pay-vs-performance / governance facts (scalars +
executive_compensation / pay_vs_performance time series) and the HTML-extracted comp tables
(summary comp, director comp, beneficial ownership, voting proposals, CEO pay ratio, audit fees).
Core U52a accessions (edge-case forms land in U52b):

  amd     rich large-cap: full PVP, every HTML table incl. director comp, pay ratio (ratio only)
  adobe   rich large-cap: full pay ratio (median present), no director-comp table extracted
  adams   closed-end fund proxy: has_xbrl FALSE -> all comp scalars/tables empty (degradation)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_AMD = "0001193125-26-129057"
_ADOBE = "0000796343-26-000043"
_ADAMS = "0001104659-26-016993"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "ProxyStatement"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "proxy"
    return body


def test_proxy_amd_rich(client: TestClient, golden) -> None:
    body = _data(client, _AMD)
    data = body["data"]
    assert body["company"] == "ADVANCED MICRO DEVICES INC"
    assert body["form"] == "DEF 14A"
    assert data["form"] == "DEF 14A"
    assert data["has_xbrl"] is True
    assert data["cik"] == "2488"  # proxy.cik as filed, not zero-padded

    # pay-vs-performance headline scalars from the XBRL ecd: facts (most-recent year)
    assert data["peo_name"] == "Lisa Su"
    assert data["peo_total_comp"] == 55161779.0
    assert data["net_income"] == 4335000000.0
    assert data["total_shareholder_return"] == 234.0
    assert data["insider_trading_policy_adopted"] is True
    assert data["has_individual_executive_data"] is False
    assert data["performance_measures"] == [
        "Revenue",
        "1-Year Total Shareholder Return",
        "Non-GAAP EPS",
        "Free Cash Flow",
        "Non-GAAP Net Income",
    ]

    # every structured table populated (this is the fullest-coverage fixture)
    assert len(data["executive_compensation"]) == 5
    assert len(data["pay_vs_performance"]) == 5
    assert len(data["summary_compensation_table"]) == 13
    assert len(data["director_compensation_table"]) == 8
    assert len(data["beneficial_ownership"]) == 16
    assert len(data["voting_proposals"]) == 5
    assert data["awards_close_to_mnpi"] == []

    # the 5-year PvP series, oldest row first (period_end ascending), kept as the as-filed ISO date
    pvp0 = data["pay_vs_performance"][0]
    assert pvp0["fiscal_year_end"] == "2021-12-25"
    assert pvp0["peo_actually_paid_comp"] == 188407046.0
    assert pvp0["net_income"] == 3162000000.0
    assert pvp0["total_shareholder_return"] == 317.0

    # CEO pay ratio: AMD discloses the ratio but the median is not in the extracted spot -> null
    assert data["ceo_pay_ratio"] == {
        "ceo_compensation": 55161779.0,
        "median_employee_compensation": None,
        "ratio": 341,
    }
    assert data["audit_fees"] is None  # no audit-fee table extracted from this filing

    prop1 = data["voting_proposals"][0]
    assert prop1["number"] == 1
    assert prop1["description"] == "ELECTION OF DIRECTORS"
    assert prop1["proposal_type"] == "director_election"

    golden("filing", "proxy_amd_def14a", body)


def test_proxy_adobe_full_pay_ratio(client: TestClient, golden) -> None:
    body = _data(client, _ADOBE)
    data = body["data"]
    assert body["company"] == "ADOBE INC."
    assert data["form"] == "DEF 14A"
    assert data["has_xbrl"] is True
    assert data["cik"] == "796343"

    # Adobe does not tag PeoName in XBRL but the comp amount is present
    assert data["peo_name"] is None
    assert data["peo_total_comp"] == 51173935.0
    assert data["net_income"] == 7130000000.0
    assert data["total_shareholder_return"] == 67.11

    # full CEO pay ratio incl. the median employee comp (contrast AMD's null median)
    assert data["ceo_pay_ratio"] == {
        "ceo_compensation": 51173935.0,
        "median_employee_compensation": 235989.0,
        "ratio": 217,
    }
    # this filing's director-comp table is not HTML-extracted -> empty (contrast AMD's 8 rows)
    assert data["director_compensation_table"] == []
    assert len(data["summary_compensation_table"]) == 9
    assert len(data["beneficial_ownership"]) == 18
    assert len(data["voting_proposals"]) == 8

    sct0 = data["summary_compensation_table"][0]
    assert sct0["name"] == "Shantanu Narayen"
    assert sct0["year"] == 2025
    assert sct0["salary"] == 1500000.0
    assert sct0["total"] == 51173935.0

    pvp0 = data["pay_vs_performance"][0]
    assert pvp0["fiscal_year_end"] == "2021-12-03"
    assert pvp0["net_income"] == 4822000000.0
    assert pvp0["total_shareholder_return"] == 129.24

    golden("filing", "proxy_adobe_def14a", body)


def test_proxy_adams_fund_degraded(client: TestClient, golden) -> None:
    body = _data(client, _ADAMS)
    data = body["data"]
    assert body["form"] == "DEF 14A"
    assert data["form"] == "DEF 14A"

    # a closed-end fund proxy with no executive-compensation XBRL: every comp leg empties cleanly,
    # the object still parses (envelope + data served, never a 500 or a partial object)
    assert data["has_xbrl"] is False
    assert data["company_name"] is None
    assert data["peo_name"] is None
    assert data["peo_total_comp"] is None
    assert data["net_income"] is None
    assert data["performance_measures"] == []
    assert data["executive_compensation"] == []
    assert data["pay_vs_performance"] == []
    assert data["summary_compensation_table"] == []
    assert data["director_compensation_table"] == []
    assert data["beneficial_ownership"] == []
    assert data["voting_proposals"] == []
    assert data["named_executives"] == []
    assert data["awards_close_to_mnpi"] == []
    assert data["ceo_pay_ratio"] is None
    assert data["audit_fees"] is None

    golden("filing", "proxy_adams_fund_degraded", body)
