"""Integration: /filing/{accession} envelope with typed Form 10-K `data` (P4).

One `TenK` object backs 10-K and 10-K/A -> one kind (`form10k`); `form` is the variant. `data` is
LEAN: the structural item index (Items 1-16 across Parts I-IV), the signing auditor (XBRL DEI
facts), the EX-21 subsidiary list, and a financials-presence flag. Item/section TEXT lives in
/content + /sections; full statements in /filing/{accession}/xbrl. Accessions span the matrix:

  nvda      standard large-cap: full items, PwC auditor, EX-21 (Mellanox/Israel), inline XBRL
  realty    REIT: KPMG auditor, a 1000+-entry EX-21 list (real-estate holding LLCs)
  riverview bank: an auditor CHANGE -- current Aprio + prior Delap (both survive); Aprio icfr FALSE
  albemarle 10-K/A: is_amendment True, a partial amendment carrying ONLY Item 15, no EX-21
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_NVDA = "0001045810-25-000023"
_REALTY = "0000726728-25-000055"
_RIVERVIEW = "0001041368-26-000007"
_ALBEMARLE_A = "0000915913-25-000077"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "TenK"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form10k"
    return body


def _item(data: dict, number: str) -> dict:
    matches = [i for i in data["items"] if i["item"] == number]
    assert len(matches) == 1, f"item {number} not uniquely present: {[i['item'] for i in data['items']]}"
    return matches[0]


def test_tenk_nvidia_standard(client: TestClient, golden) -> None:
    body = _data(client, _NVDA)
    data = body["data"]
    assert body["company"] == "NVIDIA CORP"
    assert body["form"] == "10-K"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2025-01-26"  # fiscal year ends late January
    assert data["has_financials"] is True

    # full Item 1-16 structure, canonically ordered, titled + part-tagged from the static catalog
    assert [i["item"] for i in data["items"]] == [
        "1",
        "1A",
        "1B",
        "1C",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "7A",
        "8",
        "9",
        "9A",
        "9B",
        "9C",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
    ]
    assert _item(data, "1") == {"item": "1", "part": "I", "title": "Business"}
    assert _item(data, "1A") == {"item": "1A", "part": "I", "title": "Risk Factors"}
    assert _item(data, "7") == {"item": "7", "part": "II", "title": "Management's Discussion and Analysis (MD&A)"}
    assert _item(data, "10")["part"] == "III"
    assert _item(data, "15")["part"] == "IV"

    # signing auditor from the inline-XBRL DEI facts (single auditor -> one-entry list)
    assert data["auditors"] == [
        {
            "name": "PricewaterhouseCoopers LLP",
            "location": "San Jose, California",
            "firm_id": 238,  # PCAOB firm ID
            "icfr_attestation": True,
            "period_end": "2025-01-26",
        }
    ]

    # EX-21 subsidiaries (clean two-column table: name + jurisdiction, no ownership column)
    assert data["has_subsidiaries"] is True
    assert data["subsidiaries"][0] == {
        "name": "Mellanox Technologies, Ltd",
        "jurisdiction": "Israel",
        "ownership_pct": None,
    }
    assert len(data["subsidiaries"]) == 3

    golden("filing", "tenk_nvidia", body)


def test_tenk_realty_income_reit(client: TestClient, golden) -> None:
    body = _data(client, _REALTY)
    data = body["data"]
    assert body["company"] == "REALTY INCOME CORP"
    assert body["form"] == "10-K"
    assert data["report_period"] == "2024-12-31"
    assert data["has_financials"] is True

    assert data["auditors"] == [
        {
            "name": "KPMG LLP",
            "location": "San Diego, CA",
            "firm_id": 185,
            "icfr_attestation": True,
            "period_end": "2024-12-31",
        }
    ]

    # a sprawling EX-21: the holding LLCs behind the net-lease portfolio (1000+ entities)
    assert data["has_subsidiaries"] is True
    assert len(data["subsidiaries"]) == 1066  # edgar fix: header rows no longer leak (was 1088)
    # row 0 is a real subsidiary now -- edgar's EX-21 parser filters the "Entity"/"Jurisdiction of
    # Organization" header row that this filing's layout previously leaked in as row 0
    assert data["subsidiaries"][0] == {
        "name": "11990 Eastgate Blvd, LLC",
        "jurisdiction": "Delaware",
        "ownership_pct": None,
    }
    names = [s["name"] for s in data["subsidiaries"]]
    assert "Entity" not in names  # regression lock: the header row never reappears as a subsidiary

    golden("filing", "tenk_realty_income", body)


def test_tenk_riverview_bank_icfr_false(client: TestClient, golden) -> None:
    body = _data(client, _RIVERVIEW)
    data = body["data"]
    assert body["company"] == "RIVERVIEW BANCORP INC"
    assert body["form"] == "10-K"
    assert data["report_period"] == "2026-03-31"  # fiscal year ends in March

    assert data["has_financials"] is True

    # an auditor CHANGE: current Aprio + prior Delap, each tagged on its own period context.
    # Before the per-context grouping fix the wire kept only the first DEI fact and dropped Delap.
    # Aprio also did NOT attest to ICFR -- the only icfr_attestation=False fixture.
    assert data["auditors"] == [
        {
            "name": "Aprio, LLP",
            "location": "Lake Oswego, Oregon",
            "firm_id": 926,
            "icfr_attestation": False,
            "period_end": "2026-03-31",  # current fiscal year -> leads the list
        },
        {
            "name": "Delap LLP",
            "location": "Lake Oswego, Oregon",
            "firm_id": 116,
            "icfr_attestation": False,  # prior-period auditor: no ICFR attestation fact tagged
            "period_end": "2025-03-31",
        },
    ]

    golden("filing", "tenk_riverview", body)


def test_tenk_albemarle_amendment(client: TestClient, golden) -> None:
    body = _data(client, _ALBEMARLE_A)
    data = body["data"]
    assert body["company"] == "ALBEMARLE CORP"
    assert body["form"] == "10-K/A"
    assert data["is_amendment"] is True
    assert data["report_period"] == "2024-12-31"

    assert data["has_financials"] is True

    # a partial amendment: carries ONLY Item 15 (Exhibits), no other items, no EX-21 exhibit
    assert [i["item"] for i in data["items"]] == ["15"]
    assert data["items"][0] == {"item": "15", "part": "IV", "title": "Exhibits, Financial Statement Schedules"}
    assert data["has_subsidiaries"] is False
    assert data["subsidiaries"] == []

    # the amendment still carries the auditor DEI facts from its (partial) XBRL
    assert len(data["auditors"]) == 1
    assert data["auditors"][0]["name"] == "PricewaterhouseCoopers LLP"
    assert data["auditors"][0]["firm_id"] == 238

    golden("filing", "tenk_albemarle_amendment", body)
