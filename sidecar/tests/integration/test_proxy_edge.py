"""Integration (U52b): the proxy EDGE-form matrix over the one `ProxyStatement` -> kind=proxy.

U52a proved the core DEF 14A path (rich / full-pay-ratio / degraded-fund). Every 14A variant is in
edgar's PROXY_FORMS, so they ALL dispatch to ProxyStatement; what differs is the SHAPE the object
parses to. This file pins each structural class with a real filing:

  allied      DEFC14A  contested solicitation -> structured, the only edge form carrying PVP XBRL;
                       individual-exec data True; peo comp tagged 0.0 (the maybe_float 0.0-vs-null trap)
  harborone   DEFM14A  management merger proxy -> no PVP XBRL, but the canonical 3 merger vote items
                       extract cleanly (merger / merger-related compensation / adjournment)
  ecd         PRE 14A  preliminary (draft) proxy -> has_xbrl True yet NO pay-vs-performance facts;
                       a large summary-comp table whose first row has null salary/total
  aethlon     DEF 14A  individual-executive PVP data True: negative net income, a board recommendation
                       ('FOR'), and the auditor_ratification / equity_plan proposal types
  askeladden  DFAN14A  dissident additional soliciting material (SUPPLEMENTAL_FORMS) -> degraded:
                       parses to an empty ProxyStatement, never a 500
  green       PX14A6G  third-party exempt solicitation (EXEMPT_SOLICITATION_FORMS) -> degraded empty

edgar's HTML proposal-extractor over-triggers on supplemental letters (a sibling DFAN14A,
0000921895-25-001876, mis-reads date phrases as 2 "proposals"); askeladden is the clean all-empty
case used for the crisp degradation assertion.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_ALLIED = "0001140361-25-024052"  # DEFC14A, Allied Gaming & Entertainment
_HARBORONE = "0001193125-25-150745"  # DEFM14A, HarborOne Bancorp
_ECD = "0001213900-25-059780"  # PRE 14A, ECD Automotive Design
_AETHLON = "0001683168-26-000364"  # DEF 14A (individual-exec data), Aethlon Medical
_ASKELADDEN = "0001214659-25-009815"  # DFAN14A, Askeladden Capital (re AstroNova)
_GREEN = "0001214659-25-009688"  # PX14A6G, Green Century Funds


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _proxy(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "ProxyStatement"  # every 14A variant -> ProxyStatement
    assert body["data"] is not None
    assert body["data"]["kind"] == "proxy"
    return body


def _assert_fully_degraded(data: dict) -> None:
    # a supplemental/exempt solicitation parses but carries no structured proxy disclosures
    assert data["has_xbrl"] is False
    assert data["company_name"] is None
    assert data["peo_name"] is None
    assert data["peo_total_comp"] is None
    assert data["peo_actually_paid_comp"] is None
    assert data["neo_avg_total_comp"] is None
    assert data["neo_avg_actually_paid_comp"] is None
    assert data["net_income"] is None
    assert data["total_shareholder_return"] is None
    assert data["peer_group_tsr"] is None
    assert data["fiscal_year_end"] is None
    assert data["company_selected_measure"] is None
    assert data["company_selected_measure_value"] is None
    assert data["insider_trading_policy_adopted"] is None
    assert data["award_timing_mnpi_considered"] is None
    assert data["award_dates_predetermined"] is None
    assert data["mnpi_disclosure_timed_for_comp_value"] is None
    assert data["has_individual_executive_data"] is False
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


def test_proxy_defc14a_contested(client: TestClient, golden) -> None:
    body = _proxy(client, _ALLIED)
    data = body["data"]
    assert data["form"] == "DEFC14A"
    assert data["cik"] == "1708341"
    assert data["company_name"] == "ALLIED GAMING & ENTERTAINMENT, INC."
    assert data["has_xbrl"] is True

    # the only edge form that carries pay-vs-performance XBRL
    assert data["has_individual_executive_data"] is True
    assert data["peo_total_comp"] == 0.0  # tagged 0, not null: edgar maybe_float(blank)->0.0
    assert data["peo_actually_paid_comp"] == 0.0
    assert data["net_income"] is None
    assert data["total_shareholder_return"] == 46.2
    assert data["insider_trading_policy_adopted"] is True

    assert len(data["executive_compensation"]) == 4
    assert len(data["pay_vs_performance"]) == 4
    assert len(data["summary_compensation_table"]) == 4
    assert len(data["voting_proposals"]) == 5
    assert data["beneficial_ownership"] == []
    assert data["director_compensation_table"] == []

    exec0 = data["executive_compensation"][0]
    assert exec0["fiscal_year_end"] == "2021-12-31"
    assert exec0["peo_total_comp"] == 0.0
    assert exec0["neo_avg_total_comp"] == 614383.0
    assert exec0["neo_avg_actually_paid_comp"] == 614834.0

    sct0 = data["summary_compensation_table"][0]
    assert sct0["name"] == "Yinghua Chen(2)Former"
    assert sct0["title"] == "CEO"
    assert sct0["year"] == 2024
    assert sct0["salary"] == 300000.0
    assert sct0["total"] == 1579200.0

    assert data["voting_proposals"][0]["number"] == 1
    assert data["voting_proposals"][0]["description"] == "Election of Class B Directors"
    assert data["voting_proposals"][0]["proposal_type"] == "company_proposal"
    assert data["voting_proposals"][2]["proposal_type"] == "say_on_pay"

    assert data["ceo_pay_ratio"] is None
    assert data["audit_fees"] is None
    golden("filing", "proxy_allied_defc14a", body)


def test_proxy_defm14a_merger(client: TestClient, golden) -> None:
    body = _proxy(client, _HARBORONE)
    data = body["data"]
    assert data["form"] == "DEFM14A"
    assert data["cik"] == "1769617"

    # a merger proxy carries no pay-vs-performance XBRL; the structured value is the vote slate
    assert data["has_xbrl"] is False
    assert data["company_name"] is None
    assert data["peo_total_comp"] is None
    assert data["net_income"] is None
    assert data["executive_compensation"] == []
    assert data["pay_vs_performance"] == []
    assert data["summary_compensation_table"] == []

    assert len(data["voting_proposals"]) == 3
    descriptions = [p["description"] for p in data["voting_proposals"]]
    assert descriptions == [
        "MERGER PROPOSAL",
        "MERGER-RELATED COMPENSATION PROPOSAL",
        "ADJOURNMENT PROPOSAL",
    ]
    assert data["ceo_pay_ratio"] is None
    assert data["audit_fees"] is None
    golden("filing", "proxy_harborone_defm14a", body)


def test_proxy_pre14a_preliminary(client: TestClient, golden) -> None:
    body = _proxy(client, _ECD)
    data = body["data"]
    assert data["form"] == "PRE 14A"
    assert data["cik"] == "1922858"
    assert data["company_name"] == "ECD AUTOMOTIVE DESIGN, INC."

    # has XBRL (cover/dei tags) but NO pay-vs-performance facts -> every PVP scalar null
    assert data["has_xbrl"] is True
    assert data["has_individual_executive_data"] is False
    assert data["peo_name"] is None
    assert data["peo_total_comp"] is None
    assert data["net_income"] is None
    assert data["total_shareholder_return"] is None
    assert data["executive_compensation"] == []
    assert data["pay_vs_performance"] == []

    # the HTML summary-comp table IS extracted; its first row has null salary/total (draft filing)
    assert len(data["summary_compensation_table"]) == 14
    assert len(data["voting_proposals"]) == 6
    sct0 = data["summary_compensation_table"][0]
    assert sct0["name"] == "Elliot Humble"
    assert sct0["year"] == 2023
    assert sct0["salary"] is None
    assert sct0["total"] is None

    assert data["voting_proposals"][0]["number"] == 1
    assert data["voting_proposals"][0]["description"] == "REVERSE SPLIT PROPOSAL"
    assert data["ceo_pay_ratio"] is None
    golden("filing", "proxy_ecd_pre14a", body)


def test_proxy_def14a_individual_exec_data(client: TestClient, golden) -> None:
    body = _proxy(client, _AETHLON)
    data = body["data"]
    assert data["form"] == "DEF 14A"
    assert data["cik"] == "882291"
    assert data["company_name"] == "AETHLON MEDICAL, INC."
    assert data["has_xbrl"] is True

    # the has_individual_executive_data=True branch: per-executive PVP rows, negative net income
    assert data["has_individual_executive_data"] is True
    assert data["net_income"] == -13400000.0
    assert data["total_shareholder_return"] == 2.45
    assert data["insider_trading_policy_adopted"] is True

    assert len(data["executive_compensation"]) == 3
    assert len(data["pay_vs_performance"]) == 3
    assert len(data["summary_compensation_table"]) == 6
    assert len(data["voting_proposals"]) == 7

    # peo comp is null in the year with no principal-officer tag, present in the next
    exec1 = data["executive_compensation"][1]
    assert exec1["fiscal_year_end"] == "2024-12-31"
    assert exec1["peo_total_comp"] == 505332.0
    assert exec1["peo_actually_paid_comp"] == 395249.0

    pvp0 = data["pay_vs_performance"][0]
    assert pvp0["fiscal_year_end"] == "2023-12-31"
    assert pvp0["net_income"] == -12030000.0
    assert pvp0["total_shareholder_return"] == 18.84

    sct0 = data["summary_compensation_table"][0]
    assert sct0["name"] == "James B. Frakes"
    assert sct0["year"] == 2025
    assert sct0["salary"] == 500000.0
    assert sct0["total"] == 500000.0

    # the only fixture with a non-null board recommendation + these proposal types
    assert data["voting_proposals"][0]["proposal_type"] == "director_election"
    assert data["voting_proposals"][1]["proposal_type"] == "auditor_ratification"
    assert data["voting_proposals"][1]["board_recommendation"] == "FOR"
    assert data["voting_proposals"][2]["proposal_type"] == "equity_plan"
    golden("filing", "proxy_aethlon_def14a_individual", body)


def test_proxy_dfan14a_dissident_degraded(client: TestClient, golden) -> None:
    body = _proxy(client, _ASKELADDEN)
    data = body["data"]
    assert data["form"] == "DFAN14A"
    assert data["cik"] == "1815572"
    _assert_fully_degraded(data)
    golden("filing", "proxy_askeladden_dfan14a", body)


def test_proxy_px14a6g_exempt_degraded(client: TestClient, golden) -> None:
    body = _proxy(client, _GREEN)
    data = body["data"]
    assert data["form"] == "PX14A6G"
    assert data["cik"] == "877232"
    _assert_fully_degraded(data)
    golden("filing", "proxy_green_century_px14a6g", body)
