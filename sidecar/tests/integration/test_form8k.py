"""Integration: /filing/{accession} envelope with typed Form 8-K `data` (the P4 current-report payload).

An 8-K is item-structured; `data` carries the item list (with titles from the static catalog),
edgar's content_type classification, the amendment flag, press-release/earnings presence flags, and
the curated content-exhibit refs. The heavyweight EX-99.1 earnings-table parse is out of scope -
has_earnings flags it and the EX-99 exhibit is listed. Accessions span the content-type matrix:

  apple_earnings        2.02+9.01 earnings, EX-99.1, has_earnings + has_press_release
  apple_officer_change  single Item 5.02 (director_change), no exhibits
  apple_shareholder_vote 5.07+9.01 (shareholder_vote), EX-10.1/EX-10.2 exhibits
  amh_debt_offering     8.01+9.01 classified debt_offering via the EX-1.1 exhibit-type signal
  carmart_material_agreement single Item 1.01 (material_agreement), no exhibits
  dana_amendment        8-K/A: is_amendment True, 5.02+9.01

(An M&A Item 2.01 / asset_change 8-K was not present in the sampled 2026 Q2 set; the classifier
branch is structurally identical to the captured content types.)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_APPLE_EARNINGS = "0000320193-26-000011"
_APPLE_OFFICER = "0001140361-26-015711"
_APPLE_VOTE = "0001140361-26-006577"
_AMH_DEBT = "0001104659-26-073560"
_CARMART_AGREEMENT = "0001171843-26-004099"
_DANA_AMENDMENT = "0001193125-26-268470"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "CurrentReport"
    assert body["form"].startswith("8-K")
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form8k"
    return body


def _items(data: dict) -> list[str]:
    return [item["item"] for item in data["items"]]


def test_form8k_apple_earnings(client: TestClient, golden) -> None:
    body = _data(client, _APPLE_EARNINGS)
    data = body["data"]
    assert body["company"] == "Apple Inc."
    assert data["form"] == "8-K"
    assert data["is_amendment"] is False
    assert data["content_type"] == "earnings"
    assert data["date_of_report"] == "April 30, 2026"
    assert _items(data) == ["2.02", "9.01"]
    # item titles resolve from the static 8-K catalog
    assert data["items"][0]["title"] == "Results of Operations and Financial Condition"
    # earnings 8-K: Item 2.02 + a parseable EX-99.1 press release
    assert data["has_press_release"] is True
    assert data["has_earnings"] is True
    assert len(data["exhibits"]) == 1
    assert data["exhibits"][0]["document_type"] == "EX-99.1"
    assert data["exhibits"][0]["document"] == "a8-kex991q2202603282026.htm"

    golden("filing", "form8k_apple_earnings", body)


def test_form8k_apple_officer_change(client: TestClient, golden) -> None:
    body = _data(client, _APPLE_OFFICER)
    data = body["data"]
    assert data["content_type"] == "director_change"
    assert data["date_of_report"] == "April 17, 2026"
    # single-item 8-K, no exhibits, not an earnings/press-release filing
    assert _items(data) == ["5.02"]
    assert data["items"][0]["title"].startswith("Departure of Directors")
    assert data["has_press_release"] is False
    assert data["has_earnings"] is False
    assert data["exhibits"] == []

    golden("filing", "form8k_apple_officer_change", body)


def test_form8k_apple_shareholder_vote(client: TestClient, golden) -> None:
    body = _data(client, _APPLE_VOTE)
    data = body["data"]
    assert data["content_type"] == "shareholder_vote"
    assert _items(data) == ["5.07", "9.01"]
    assert data["items"][0]["title"] == "Submission of Matters to a Vote of Security Holders"
    # two EX-10 material-contract exhibits
    assert [ex["document_type"] for ex in data["exhibits"]] == ["EX-10.1", "EX-10.2"]
    assert data["has_earnings"] is False

    golden("filing", "form8k_apple_shareholder_vote", body)


def test_form8k_amh_debt_offering(client: TestClient, golden) -> None:
    body = _data(client, _AMH_DEBT)
    data = body["data"]
    assert body["company"] == "American Homes 4 Rent"
    # content_type uses the EX-1.1 exhibit-type signal to classify an 8.01 filing as debt_offering
    assert data["content_type"] == "debt_offering"
    assert _items(data) == ["8.01", "9.01"]
    assert [ex["document_type"] for ex in data["exhibits"]] == ["EX-1.1", "EX-5.1"]

    golden("filing", "form8k_amh_debt_offering", body)


def test_form8k_carmart_material_agreement(client: TestClient, golden) -> None:
    body = _data(client, _CARMART_AGREEMENT)
    data = body["data"]
    assert body["company"] == "AMERICAS CARMART INC"
    assert data["content_type"] == "material_agreement"
    assert _items(data) == ["1.01"]
    assert data["items"][0]["title"] == "Entry into a Material Definitive Agreement"
    assert data["exhibits"] == []

    golden("filing", "form8k_carmart_material_agreement", body)


def test_form8k_dana_amendment(client: TestClient, golden) -> None:
    body = _data(client, _DANA_AMENDMENT)
    data = body["data"]
    assert body["company"] == "DANA Inc"
    assert body["form"] == "8-K/A"
    # the object reports the amendment via both the form suffix and the flag
    assert data["form"] == "8-K/A"
    assert data["is_amendment"] is True
    assert data["content_type"] == "director_change"
    assert _items(data) == ["5.02", "9.01"]
    assert [ex["document_type"] for ex in data["exhibits"]] == ["EX-10.1", "EX-10.2"]

    golden("filing", "form8k_dana_amendment", body)
