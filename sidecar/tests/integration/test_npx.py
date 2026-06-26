"""Integration (U57d): the N-PX / N-PX/A proxy voting record over one NPX -> kind=npx.

N-PX is filed annually by registered investment companies (mutual funds) and institutional
managers to report their proxy voting record. Two report families: FUND VOTING/NOTICE
(mutual funds, has series) and INSTITUTIONAL MANAGER VOTING/NOTICE (investment advisers,
no series). proxy_votes can be None from edgar (notice reports) -- wire sends [].
Four fixtures pin the matrix:

  perritt      N-PX, Perritt Funds (FUND VOTING REPORT, 291 votes, 2 series)
  imst         N-PX, IMST II (FUND NOTICE REPORT, 0 votes, 6 series)
  provident    N-PX, Provident IM (IM NOTICE REPORT, 0 votes, no series)
  hbk          N-PX/A, HBK Investments (IM VOTING REPORT amendment, 0 votes)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_PERRITT = "0000897069-26-000968"  # N-PX, Perritt Funds (FUND VOTING REPORT, 291 votes, 2 series)
_IMST = "0001398344-26-009630"  # N-PX, IMST II (FUND NOTICE REPORT, 0 votes, 6 series)
_PROVIDENT = "0001076964-26-000007"  # N-PX, Provident IM (IM NOTICE REPORT, 0 votes, no series)
_HBK = "0001011443-26-000007"  # N-PX/A, HBK Investments (IM VOTING REPORT amendment, 0 votes)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _npx(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "NPX"
    assert body["data"] is not None
    assert body["data"]["kind"] == "npx"
    return body


def test_npx_fund_voting_report(client: TestClient, golden) -> None:
    body = _npx(client, _PERRITT)
    data = body["data"]
    assert data["form"] == "N-PX"
    assert data["report_type"] == "FUND VOTING REPORT"
    assert data["fund_name"] == "Perritt Funds Inc"
    assert data["is_amendment"] is False
    assert data["registrant_type"] == "RMIC"
    assert data["investment_company_type"] == "N-1A"
    assert data["series_count"] == "2"

    assert len(data["series_reports"]) == 2
    sr0 = data["series_reports"][0]
    assert sr0["id_of_series"] == "S000000859"
    assert sr0["name_of_series"] == "Perritt Ultra MicroCap Fund"
    assert sr0["lei_of_series"] is not None

    assert len(data["proxy_votes"]) == 291
    pv0 = data["proxy_votes"][0]
    assert pv0["issuer_name"] == "A-MARK PRECIOUS METALS, INC."
    assert pv0["cusip"] == "00181T107"
    assert pv0["isin"] == "US00181T1079"
    assert pv0["meeting_date"] is not None
    assert pv0["vote_source"] == "ISSUER"
    assert pv0["vote_series"] == "S000039929"
    assert pv0["vote_categories"][0]["category_type"] == "DIRECTOR ELECTIONS"
    assert pv0["vote_records"][0]["how_voted"] == "FOR"
    assert pv0["vote_records"][0]["shares_voted"] == 25000.0
    assert pv0["vote_records"][0]["management_recommendation"] == "FOR"

    golden("filing", "npx_perritt_fund", body)


def test_npx_fund_notice_report(client: TestClient, golden) -> None:
    body = _npx(client, _IMST)
    data = body["data"]
    assert data["form"] == "N-PX"
    assert data["report_type"] == "FUND NOTICE REPORT"
    assert data["fund_name"] == "Investment Managers Series Trust II"

    assert len(data["series_reports"]) == 6
    sr0 = data["series_reports"][0]
    assert sr0["id_of_series"] == "S000093736"
    assert "Tradr" in sr0["name_of_series"]

    assert len(data["report_series_class_infos"]) == 6
    rsci0 = data["report_series_class_infos"][0]
    assert rsci0["series_id"] is not None
    assert len(rsci0["class_infos"]) >= 1
    assert rsci0["class_infos"][0]["class_id"] is not None

    assert data["proxy_votes"] == []

    golden("filing", "npx_imst_notice", body)


def test_npx_im_notice_degraded(client: TestClient, golden) -> None:
    body = _npx(client, _PROVIDENT)
    data = body["data"]
    assert data["form"] == "N-PX"
    assert data["report_type"] == "INSTITUTIONAL MANAGER NOTICE REPORT"
    assert data["registrant_type"] == "IM"
    assert data["proxy_votes"] == []
    assert data["series_reports"] == []
    assert data["report_series_class_infos"] == []
    assert data["included_managers"] == []

    golden("filing", "npx_provident_im_notice", body)


def test_npx_amendment_dispatch(client: TestClient, golden) -> None:
    body = _npx(client, _HBK)
    data = body["data"]
    assert data["form"] == "N-PX/A"
    assert data["is_amendment"] is True
    assert data["amendment_no"] == "6"
    assert data["amendment_type"] == "NEW PROXY"
    assert data["proxy_votes"] == []

    golden("filing", "npx_hbk_amendment", body)
