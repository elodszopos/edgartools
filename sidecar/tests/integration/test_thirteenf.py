"""Integration: /filing/{accession} envelope with typed Form 13F `data` (P4).

One `ThirteenF` object backs the whole family -> one kind (`form13f`); the `form` field is the
variant. `data` carries the cover page (filing manager + other managers), the summary totals,
the signature, and `holdings` - the DISAGGREGATED information table (one row per security per
reporting manager, full fidelity incl. InvestmentDiscretion, OtherManager and voting splits).
Accessions span the matrix:

  bml_capital        base 13F-HR, dollars era, 16 holdings incl. one put
  pershing_square    2013 13F-HR: thousands era (values normalized x1000), 2 included managers,
                     multi-manager rows (OtherManager set), a call option, Ackman signer
  shengqi_amendment  13F-HR/A: is_amendment True, "Amendment of Investment Holdings"
  fig_notice         13F-NT: has_holdings False, holdings empty, totals zero (an affiliated
                     manager reports the holdings), but cover/summary/signature still parse
  investidor         13F-HR, dollars era, 27 holdings, several put/call option rows

13F-CTR (combination report) is in THIRTEENF_FORMS but has zero filings in EDGAR as of 2026-06.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_BML = "0001754960-26-000359"
_PERSHING = "0001172661-13-001539"
_SHENGQI = "0002040405-26-000005"
_FIG = "0001245521-26-000002"
_INVESTIDOR = "0001953154-26-000002"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "ThirteenF"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form13f"
    return body


def _put_call_rows(data: dict) -> list[dict]:
    return [h for h in data["holdings"] if h["put_call"]]


def test_thirteenf_bml_base(client: TestClient, golden) -> None:
    body = _data(client, _BML)
    data = body["data"]
    assert body["company"] == "BML Capital Management, LLC"
    assert body["form"] == "13F-HR"
    assert data["is_amendment"] is False
    assert data["has_holdings"] is True
    assert data["report_period"] == "2026-03-31"
    assert data["additional_information"] is None

    cover = data["cover_page"]
    assert cover["report_calendar_or_quarter"] == "03-31-2026"
    assert cover["report_type"] == "13F HOLDINGS REPORT"
    assert cover["filing_manager"]["name"] == "BML Capital Management, LLC"
    assert cover["filing_manager"]["address"]["state_or_country"] == "IN"
    assert cover["other_managers"] == []

    summary = data["summary"]
    assert summary["total_value"] == 155765709.0
    assert summary["total_holdings"] == 16
    assert summary["other_included_managers_count"] == 0
    assert summary["other_managers"] == []

    sig = data["signature"]
    assert sig["name"] == "Aryn Sands"
    assert sig["title"] == "Agent"
    assert sig["city"] == "Reno"
    assert sig["date"] == "05-05-2026"
    assert sig["phone"] == "844-844-3453"

    assert len(data["holdings"]) == 16
    top = data["holdings"][0]
    assert top["issuer"] == "ACLARIS THERAPEUTICS INC"
    assert top["cusip"] == "00461U105"
    assert top["ticker"] == "ACRS"
    assert top["value"] == 53437500
    assert top["shares_or_principal_amount"] == 14250000
    assert top["shares_or_principal_type"] == "Shares"
    assert top["put_call"] is None
    assert top["investment_discretion"] == "SOLE"
    assert top["other_manager"] is None
    assert top["no_voting_authority"] == 14250000

    # the single option position: put on Walmart, serialized as filed
    puts = _put_call_rows(data)
    assert len(puts) == 1
    assert puts[0]["issuer"] == "WALMART INC"
    assert puts[0]["put_call"] == "Put"
    assert puts[0]["value"] == 329138

    golden("filing", "thirteenf_bml_capital", body)


def test_thirteenf_pershing_square_thousands(client: TestClient, golden) -> None:
    body = _data(client, _PERSHING)
    data = body["data"]
    assert body["company"] == "Pershing Square Capital Management, L.P."
    assert body["form"] == "13F-HR"
    assert data["report_period"] == "2013-09-30"
    assert data["is_amendment"] is False
    assert data["has_holdings"] is True
    assert data["additional_information"] == ("PS Management GP, LLC is the general partner of Pershing Square Capital Management, L.P.")

    cover = data["cover_page"]
    assert cover["filing_manager"]["name"] == "Pershing Square Capital Management, L.P."
    assert cover["filing_manager"]["address"]["state_or_country"] == "NY"

    # 2013 is a thousands-unit filing; edgar normalizes value x1000, so totals are whole dollars
    summary = data["summary"]
    assert summary["total_value"] == 10275311000.0
    assert summary["total_holdings"] == 17
    assert summary["other_included_managers_count"] == 2
    # the "list of other included managers" from the summary page (distinct from the cover list)
    assert len(summary["other_managers"]) == 2
    assert summary["other_managers"][0] == {
        "cik": "0001336476",
        "name": "Pershing Square GP, LLC",
        "file_number": "028-11695",
        "sequence_number": 1,
    }
    assert summary["other_managers"][1]["name"] == "PS V GP, LLC"
    assert summary["other_managers"][1]["file_number"] is None
    assert summary["other_managers"][1]["sequence_number"] == 2

    assert data["signature"]["name"] == "William A Ackman"
    assert data["signature"]["title"] == "Managing Member of PS Management GP, LLC"
    assert data["signature"]["date"] == "11-14-2013"

    assert len(data["holdings"]) == 17
    top = data["holdings"][0]
    assert top["issuer"] == "AIR PRODS & CHEMS INC"
    assert top["cusip"] == "009158106"
    assert top["ticker"] == "APD"
    # thousands normalization proof: as-filed value 810053 (thousands) -> 810,053,000 dollars
    assert top["value"] == 810053000
    assert top["shares_or_principal_amount"] == 7601140
    assert top["investment_discretion"] == "OTR"
    # multi-manager filing: this row is reported under other-manager index "2"
    assert top["other_manager"] == "2"
    assert top["shared_voting_authority"] == 7601140

    # a call option, also thousands-normalized
    calls = [h for h in data["holdings"] if h["put_call"] == "Call"]
    assert any(h["issuer"] == "PROCTER & GAMBLE CO" and h["value"] == 1227597000 for h in calls)

    golden("filing", "thirteenf_pershing_square", body)


def test_thirteenf_shengqi_amendment(client: TestClient, golden) -> None:
    body = _data(client, _SHENGQI)
    data = body["data"]
    assert body["company"] == "Shengqi Capital (Hong Kong) Ltd"
    assert body["form"] == "13F-HR/A"
    assert data["is_amendment"] is True
    assert data["has_holdings"] is True
    assert data["report_period"] == "2026-03-31"
    assert data["additional_information"] == "Amendment of Investment Holdings"

    summary = data["summary"]
    assert summary["total_value"] == 67608897.0
    assert summary["total_holdings"] == 5

    assert len(data["holdings"]) == 5
    top = data["holdings"][0]
    assert top["issuer"] == "ALPHABET INC"
    assert top["cusip"] == "02079K107"
    assert top["ticker"] == "GOOG"
    assert top["value"] == 28686
    assert top["shares_or_principal_amount"] == 100
    assert top["sole_voting_authority"] == 100

    golden("filing", "thirteenf_shengqi_amendment", body)


def test_thirteenf_fig_notice_no_holdings(client: TestClient, golden) -> None:
    body = _data(client, _FIG)
    data = body["data"]
    assert body["company"] == "FIG LLC"
    assert body["form"] == "13F-NT"
    # a 13F-NT is a notice: an affiliated manager reports the holdings, so this filing has none
    assert data["has_holdings"] is False
    assert data["holdings"] == []
    assert data["is_amendment"] is False
    assert data["report_period"] == "2026-03-31"

    # cover/summary/signature still parse - the notice carries no information table, not no document
    cover = data["cover_page"]
    assert cover["report_type"] == "13F NOTICE"
    assert cover["filing_manager"]["name"] == "FIG LLC"
    summary = data["summary"]
    assert summary["total_value"] == 0.0
    assert summary["total_holdings"] == 0
    assert data["signature"]["name"] == "David Brooks"
    assert data["signature"]["title"] == "General Counsel and VP"

    golden("filing", "thirteenf_fig_notice", body)


def test_thirteenf_investidor_options(client: TestClient, golden) -> None:
    body = _data(client, _INVESTIDOR)
    data = body["data"]
    assert body["company"] == "Investidor Profissional Gestao de Recursos Ltda."
    assert body["form"] == "13F-HR"
    assert data["has_holdings"] is True
    assert data["report_period"] == "2026-03-31"

    summary = data["summary"]
    assert summary["total_value"] == 305826136.0
    assert summary["total_holdings"] == 27

    assert len(data["holdings"]) == 27
    top = data["holdings"][0]
    assert top["issuer"] == "AIRBNB INC"
    assert top["cusip"] == "009066101"
    assert top["ticker"] == "ABNB"
    assert top["value"] == 2516508
    assert top["shares_or_principal_amount"] == 19928

    # several option rows; at least one Amazon call, serialized as filed
    calls = [h for h in data["holdings"] if h["put_call"] == "Call"]
    assert any(h["issuer"] == "AMAZON COM INC" and h["value"] == 708118 for h in calls)

    golden("filing", "thirteenf_investidor", body)
