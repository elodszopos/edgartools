"""Integration (U57b): the N-CEN annual fund census over one `FundCensus` -> kind=ncen.

N-CEN has ZERO XBRL -- edgar lxml-parses the submission XML into a registrant block (identity +
governance: directors, CCO, accountant, underwriter) and a per-series tree (service providers, broker-
dealers + brokers, principal transactions, securities-lending agents, line of credit, liquidity
classification services, and ETF mechanics with authorized participants). Three fixtures pin the matrix:

  bny_mellon    single-series traditional fund: full governance + every provider list, broker_dealers
                AND brokers, a securities-lending agent, TWO line-of-credit facilities (committed +
                uncommitted), and 4 share classes. A broker-dealer files file_number/lei as the literal
                "N/A" sentinel (edgar keeps it; only CRD is nulled)
  advisor_etf   ETF trust: 3 series of which 2 are exchange-traded -> etf_info with authorized
                participants, exchange/ticker, in-kind percentages (is_in_kind True)
  axonic_amend  N-CEN/A amendment (dispatch via the "/A" form): a non-diversified single series

Every Decimal crosses as float|None; total_series as int|None; dates/ids/names as as-filed text. The
"Y"/"N" flags cross as bool; is_diversified is tri-state (True/False here). A line of credit carries a
LIST of facilities, each with as-filed text `is_committed` ("Committed"/"Uncommitted"), NOT a bool.
Share classes (id/name/ticker) come from the SGML header's class-contract block, joined per series.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_BNY = "0001752724-25-058074"  # N-CEN, BNY Mellon Investment Funds V (governance + providers + LoC)
_ADVISOR = "0001145549-25-040051"  # N-CEN, Advisor Managed Portfolios (ETF trust, in-kind APs)
_AXONIC = "0001752724-25-067759"  # N-CEN/A, Axonic Funds (amendment, non-diversified series)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _ncen(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "FundCensus"  # every N-CEN (+/A) -> this one object
    assert body["data"] is not None
    assert body["data"]["kind"] == "ncen"
    return body


def test_ncen_traditional_fund_governance_providers(client: TestClient, golden) -> None:
    body = _ncen(client, _BNY)
    data = body["data"]
    assert data["form"] == "N-CEN"
    assert data["report_date"] == "2024-12-31"  # reportEndingPeriod, as-filed text
    assert data["is_period_lt_12_months"] is False

    reg = data["registrant"]
    assert reg["name"] == "BNY Mellon Investment Funds V, Inc."
    assert reg["cik"] == "0000881773"
    assert reg["lei"] == "549300E6YYE1FQWV1O19"
    assert reg["file_number"] == "811-06490"
    assert reg["classification_type"] == "N-1A"
    assert reg["total_series"] == 2  # registrant has 2 series total; only 1 is in THIS filing
    assert reg["city"] == "New York"
    assert reg["state"] == "US-NY"
    assert reg["zip_code"] == "10286"
    assert reg["cco_name"] == "Joseph W. Connolly"
    assert reg["cco_crd"] == "001144952"
    assert reg["underwriter_name"] == "BNY Mellon Securities Corporation"
    assert len(reg["directors"]) == 8
    assert all(d["is_interested_person"] is False for d in reg["directors"])  # fully independent board
    assert reg["directors"][0]["name"] == "Gina D. France"
    assert reg["directors"][0]["crd_number"] is None
    assert reg["accountant"] == {
        "name": "Ernst & Young LLP",
        "pcaob_number": "42",
        "lei": "254900H1VLSDPE6LJK37",
    }

    assert data["signature_info"] == {
        "registrant_name": "BNY Mellon Investment Funds V, Inc.",
        "signed_date": "2025-03-14",
        "signer": "Amanda Quinn",
        "title": "Vice President and Assistant Secretary",
    }

    assert len(data["series"]) == 1  # only one series in this filing (num_series < total_series)
    s = data["series"][0]
    assert s["name"] == "BNY Mellon Large Cap Equity Fund"
    assert s["series_id"] == "S000019789"
    assert s["is_diversified"] is True
    assert s["avg_net_assets"] == 290767802.0
    assert s["aggregate_commission"] == 62561.0
    assert s["is_securities_lending"] is True

    assert s["advisers"][0] == {
        "name": "BNY Mellon Investment Adviser, Inc.",
        "role": "adviser",
        "lei": "54930067A504FBYASH16",
        "file_number": "801-8147",
        "crd_number": "000105642",
        "is_affiliated": False,
    }
    assert s["custodians"][0]["name"] == "The Bank of New York Mellon"
    assert s["custodians"][0]["is_affiliated"] is True

    # a broker-dealer files file_number + lei as the literal "N/A" -- edgar keeps it (only CRD is nulled)
    assert len(s["broker_dealers"]) == 17
    bd = s["broker_dealers"][0]
    assert bd["file_number"] == "N/A"
    assert bd["lei"] == "N/A"
    assert bd["crd_number"] is None
    assert bd["commission"] == 0.0

    assert len(s["brokers"]) == 10
    assert s["brokers"][0] == {
        "name": "RBC CAPITAL MARKETS, LLC",
        "file_number": "008-45411",
        "crd_number": "000031194",
        "lei": "549300LCO2FLSSVFFR64",
        "commission": 2826.0,
    }
    assert len(s["principal_transactions"]) == 10
    assert s["principal_transactions"][0]["total_purchase_sale"] == 9714802.0

    assert len(s["securities_lending"]) == 1
    assert s["securities_lending"][0] == {
        "agent_name": "The Bank of New York Mellon",
        "agent_lei": "HPFHU0OQ28E4N0NFVK49",
        "is_affiliated": True,
        "is_indemnified": True,
    }
    # TWO credit facilities filed (committed + uncommitted, different lenders) -- both carried, not
    # flattened to the first. per-facility is_committed is as-filed TEXT, not a bool.
    assert s["line_of_credit"] == {
        "has_line_of_credit": True,
        "facilities": [
            {"is_committed": "Committed", "size": 738000000.0, "institution_names": ["Citibank, N.A"]},
            {"is_committed": "Uncommitted", "size": 300000000.0, "institution_names": ["The Bank of New York Mellon"]},
        ],
    }
    assert s["etf_info"] is None  # not an ETF series

    # all 4 share classes from the SGML header's class-contract block (id/name/ticker), joined per series
    assert s["share_classes"] == [
        {"class_id": "C000055454", "class_name": "Class A", "class_ticker": "DLQAX"},
        {"class_id": "C000055455", "class_name": "Class C", "class_ticker": "DEYCX"},
        {"class_id": "C000055456", "class_name": "Class I", "class_ticker": "DLQIX"},
        {"class_id": "C000163518", "class_name": "Class Y", "class_ticker": "DLACX"},
    ]

    golden("filing", "ncen_bny_mellon", body)


def test_ncen_etf_trust_authorized_participants(client: TestClient, golden) -> None:
    body = _ncen(client, _ADVISOR)
    data = body["data"]
    assert data["form"] == "N-CEN"
    assert data["report_date"] == "2025-03-31"

    reg = data["registrant"]
    assert reg["name"] == "Advisor Managed Portfolios"
    assert reg["cik"] == "0001970751"
    assert reg["total_series"] == 15
    assert reg["underwriter_name"] == "Quasar Distributors, LLC"
    # an interested (affiliated) director -> the is_interested_person True path
    assert reg["directors"][0]["name"] == "Christopher E. Kashmerick"
    assert reg["directors"][0]["is_interested_person"] is True
    # accountant LEI filed as literal "N/A" (kept as-is, not nulled)
    assert reg["accountant"]["name"] == "Cohen & Company, Ltd."
    assert reg["accountant"]["lei"] == "N/A"

    assert len(data["series"]) == 3
    etf_series = [s for s in data["series"] if s["etf_info"] is not None]
    assert len(etf_series) == 2

    cornercap = next(s for s in data["series"] if s["name"] == "CornerCap Fundametrics Large-Cap ETF")
    assert cornercap["series_id"] == "S000082979"
    # an ETF series carries its single share class from the SGML header (the ETF itself)
    assert cornercap["share_classes"] == [
        {"class_id": "C000246426", "class_name": "CornerCap Fundametrics Large-Cap ETF", "class_ticker": "FUNL"},
    ]
    etf = cornercap["etf_info"]
    assert etf["series_id"] == "S000082979"
    assert etf["fund_name"] == "CornerCap Fundametrics Large-Cap ETF"
    assert etf["exchange"] == "CBSX"
    assert etf["ticker"] == "FUNL"
    assert etf["creation_unit_size"] == 15000.0
    assert etf["is_in_kind"] is True
    assert etf["avg_pct_purchased_in_kind"] == 15.32
    assert etf["avg_pct_redeemed_in_kind"] == 98.61
    assert len(etf["authorized_participants"]) == 4
    assert etf["authorized_participants"][0] == {
        "name": "RBC CAPITAL MARKETS, LLC",
        "lei": "549300LCO2FLSSVFFR64",
        "file_number": "8-45411",
        "crd_number": "000031194",
        "purchase_value": 34325613.0,
        "redeem_value": 42999346.5,
    }

    golden("filing", "ncen_advisor_etf", body)


def test_ncen_amendment_non_diversified(client: TestClient, golden) -> None:
    body = _ncen(client, _AXONIC)
    data = body["data"]
    assert data["form"] == "N-CEN/A"  # amendment dispatches through NCEN_FORMS
    assert data["report_date"] == "2024-10-31"

    reg = data["registrant"]
    assert reg["name"] == "Axonic Funds"
    assert reg["cik"] == "0001791032"
    assert reg["total_series"] == 1

    assert len(data["series"]) == 1
    s = data["series"][0]
    assert s["name"] == "Axonic Strategic Income Fund"
    assert s["series_id"] == "S000067475"
    assert s["is_diversified"] is False  # non-diversified -> the False tri-state
    # single uncommitted facility (genuinely one, not a flattened multi)
    assert s["line_of_credit"]["facilities"] == [
        {"is_committed": "Uncommitted", "size": 250000000.0, "institution_names": ["U.S. Bank NA"]},
    ]
    assert s["etf_info"] is None
    # two share classes, neither with a ticker (joined from the SGML header)
    assert s["share_classes"] == [
        {"class_id": "C000216959", "class_name": "Class A Shares", "class_ticker": None},
        {"class_id": "C000216960", "class_name": "Class I Shares", "class_ticker": None},
    ]

    golden("filing", "ncen_axonic_amend", body)
