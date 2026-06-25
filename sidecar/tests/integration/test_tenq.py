"""Integration: /filing/{accession} envelope with typed Form 10-Q `data` (P4).

One `TenQ` object backs 10-Q and 10-Q/A -> one kind (`form10q`); `form` is the variant. `data` is
LEAN: the part-qualified item index (Part I Items 1-4, Part II Items 1-6), the signing auditor
(usually null -- 10-Q financials are unaudited), and a financials-presence flag. There is no EX-21
subsidiary list (a 10-K-only exhibit). Item/section TEXT lives in /content + /sections; full
statements in /filing/{accession}/xbrl. The defining 10-Q trait vs the 10-K: the same item number
recurs across parts, so Part I Item 1 ("Financial Statements") and Part II Item 1 ("Legal
Proceedings") are distinct -- the converter resolves the title PART-AWARE. Accessions span:

  aapl      standard mega-cap, fiscal-year offset (Dec quarter): full Part I + Part II items
  sandisk   10-Q/A: is_amendment True, a partial amendment missing Part I Item 1 (no restated financials)
  riverview bank: same issuer as the U46 10-K bank fixture (10-K vs 10-Q produce distinct kinds)
  realty    REIT: same issuer as the U46 10-K REIT fixture
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_AAPL = "0000320193-26-000006"
_SANDISK_A = "0002023554-25-000016"
_RIVERVIEW = "0000939057-25-000048"
_REALTY = "0000726728-26-000030"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "TenQ"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form10q"
    return body


def _pairs(data: dict) -> set[tuple[str | None, str]]:
    # edgar emits items in section-detection order (not sorted), so key on (part, item) pairs
    return {(i["part"], i["item"]) for i in data["items"]}


def _item(data: dict, part: str, number: str) -> dict:
    matches = [i for i in data["items"] if i["part"] == part and i["item"] == number]
    assert len(matches) == 1, f"Part {part} Item {number} not uniquely present: {sorted(_pairs(data))}"
    return matches[0]


def test_tenq_apple_standard(client: TestClient, golden) -> None:
    body = _data(client, _AAPL)
    data = body["data"]
    assert body["company"] == "Apple Inc."
    assert body["form"] == "10-Q"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2025-12-27"  # Q1 FY2026 (fiscal year ends late September)
    assert data["has_financials"] is True
    assert data["auditor"] is None  # 10-Q is unaudited -> no DEI auditor facts tagged
    assert data["auditors"] == []

    # full quarterly structure: Part I Items 1-4 + Part II Items 1,1A,2-6
    assert _pairs(data) == {
        ("I", "1"),
        ("I", "2"),
        ("I", "3"),
        ("I", "4"),
        ("II", "1"),
        ("II", "1A"),
        ("II", "2"),
        ("II", "3"),
        ("II", "4"),
        ("II", "5"),
        ("II", "6"),
    }

    # the defining 10-Q trait: Item 1 means different things in each part (part-AWARE title lookup)
    assert _item(data, "I", "1")["title"] == "Financial Statements"
    assert _item(data, "II", "1")["title"] == "Legal Proceedings"
    assert _item(data, "II", "1A")["title"] == "Risk Factors"
    assert _item(data, "I", "2")["title"] == "Management's Discussion and Analysis of Financial Condition and Results of Operations (MD&A)"

    # items arrive in detection order (NOT sorted by part/number)
    assert [f"{i['part']},{i['item']}" for i in data["items"]] == [
        "I,1", "I,3", "I,4", "II,1", "II,1A", "II,2", "II,3", "II,4", "II,5", "II,6", "I,2",
    ]

    golden("filing", "tenq_apple", body)


def test_tenq_sandisk_amendment(client: TestClient, golden) -> None:
    body = _data(client, _SANDISK_A)
    data = body["data"]
    assert body["company"] == "Sandisk Corp"
    assert body["form"] == "10-Q/A"
    assert data["is_amendment"] is True
    assert data["report_period"] == "2024-12-27"
    assert data["auditor"] is None
    assert data["auditors"] == []
    assert data["has_financials"] is True

    # a partial amendment: restates MD&A / risk factors but NOT the Part I Item 1 financial statements
    assert ("I", "1") not in _pairs(data)
    assert _item(data, "II", "1A")["title"] == "Risk Factors"
    assert _item(data, "I", "2")["title"] == "Management's Discussion and Analysis of Financial Condition and Results of Operations (MD&A)"

    golden("filing", "tenq_sandisk_amendment", body)


def test_tenq_riverview_bank(client: TestClient, golden) -> None:
    body = _data(client, _RIVERVIEW)
    data = body["data"]
    assert body["company"] == "RIVERVIEW BANCORP INC"
    assert body["form"] == "10-Q"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2024-12-31"  # fiscal year ends in March -> Dec quarter is Q3
    assert data["has_financials"] is True
    assert data["auditor"] is None
    assert data["auditors"] == []

    # same issuer as the U46 10-K bank fixture: the 10-Q yields a DISTINCT kind + part-qualified items
    assert len(data["items"]) >= 4
    assert _item(data, "I", "1")["title"] == "Financial Statements"
    assert _item(data, "II", "1")["title"] == "Legal Proceedings"

    golden("filing", "tenq_riverview", body)


def test_tenq_realty_income_reit(client: TestClient, golden) -> None:
    body = _data(client, _REALTY)
    data = body["data"]
    assert body["company"] == "REALTY INCOME CORP"
    assert body["form"] == "10-Q"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2026-03-31"  # Q1 2026
    assert data["has_financials"] is True
    assert data["auditor"] is None
    assert data["auditors"] == []

    assert len(data["items"]) >= 4
    assert _item(data, "I", "1")["title"] == "Financial Statements"
    assert _item(data, "II", "1A")["title"] == "Risk Factors"

    golden("filing", "tenq_realty_income", body)
