"""Integration: /filing/{accession} envelope with typed Form 20-F `data` (P4).

One `TwentyF` object backs 20-F and 20-F/A -> one kind (`form20f`); `form` is the variant. Like the
10-K (and unlike the 10-Q), 20-F item numbers are UNIQUE across the form's five Parts, so the
converter titles/parts each via the static SEC 20-F catalog -- the same `report_item_from_catalog`
path the 10-K uses. `data` is LEAN: the catalog-titled item index, the signing auditor (foreign
private issuers DO tag DEI auditor facts -- unlike the unaudited 10-Q), and a financials-presence
flag. Item TEXT lives in /content + /sections; full statements in /filing/{accession}/xbrl. Gotchas
captured here: items arrive in section-DETECTION order (Check Point's first emitted item is 17, not
1), and sub-items beyond the catalog (16A-16K, 10J) resolve to part=null/title=null -- detected but
untitled, never synthesized. Accessions span:

  braskem    Brazil/IFRS mega-cap: full Item 1-19 structure (28 detected), KPMG Brazil auditor
  checkpoint Israeli tech: 31 items incl. 4A (titled catalog sub-item) + 16F (present, unlike braskem)
  cellectis  20-F/A: is_amendment True, partial amendment (only Item 19); an auditor CHANGE -- current
             KPMG France + prior Ernst & Young (both survive the per-context grouping)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_BRASKEM = "0001292814-25-001192"
_CHECKPOINT = "0001178913-26-001932"
_CELLECTIS_A = "0001193125-25-054874"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "TwentyF"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form20f"
    return body


def _by_num(data: dict) -> dict[str, dict]:
    # 20-F item numbers are unique across Parts (unlike the part-qualified 10-Q); edgar emits them in
    # detection order, so key on item number rather than position
    return {i["item"]: i for i in data["items"]}


def test_twentyf_braskem_brazil_ifrs(client: TestClient, golden) -> None:
    body = _data(client, _BRASKEM)
    data = body["data"]
    assert body["company"] == "BRASKEM SA"
    assert body["form"] == "20-F"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2024-12-31"
    assert data["has_financials"] is True
    # foreign private issuers tag DEI auditor facts (contrast: the unaudited 10-Q tags none)
    assert data["auditors"] == [
        {
            "name": "KPMG Auditores Independentes Ltda.",
            "location": "São Paulo",
            "firm_id": 1124,
            "icfr_attestation": True,
            "period_end": "2024-12-31",
        }
    ]

    items = _by_num(data)
    assert len(data["items"]) == 28
    # catalog-titled items, part-resolved across the five Parts
    assert items["3"] == {"item": "3", "part": "I", "title": "Key Information"}
    assert items["5"]["part"] == "II"
    assert items["5"]["title"] == "Operating and Financial Review and Prospects"
    assert items["19"] == {"item": "19", "part": "V", "title": "Exhibits"}
    # sub-items beyond the static catalog: detected but untitled
    assert items["16A"] == {"item": "16A", "part": None, "title": None}
    # this filer omits 16F (Check Point carries it) -- the index reflects what's detected, nothing synthesized
    assert "16F" not in items

    golden("filing", "twentyf_braskem", body)


def test_twentyf_checkpoint_tech(client: TestClient, golden) -> None:
    body = _data(client, _CHECKPOINT)
    data = body["data"]
    assert body["company"] == "CHECK POINT SOFTWARE TECHNOLOGIES LTD"
    assert body["form"] == "20-F"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2025-12-31"
    assert data["has_financials"] is True
    assert data["auditors"] == [
        {
            "name": "Kost Forer Gabbay & Kasierer",
            "location": "Tel-Aviv, Israel",
            "firm_id": 1281,
            "icfr_attestation": True,
            "period_end": "2025-12-31",
        }
    ]

    items = _by_num(data)
    assert len(data["items"]) == 31
    # 4A is a catalog sub-item that IS titled (contrast the 16-series sub-items below)
    assert items["4A"] == {"item": "4A", "part": "I", "title": "Unresolved Staff Comments"}
    # 16F present here, absent for braskem; both untitled (beyond the catalog)
    assert items["16F"] == {"item": "16F", "part": None, "title": None}
    assert items["10J"] == {"item": "10J", "part": None, "title": None}

    golden("filing", "twentyf_checkpoint", body)


def test_twentyf_cellectis_amendment(client: TestClient, golden) -> None:
    body = _data(client, _CELLECTIS_A)
    data = body["data"]
    assert body["company"] == "Cellectis S.A."
    assert body["form"] == "20-F/A"
    assert data["is_amendment"] is True
    assert data["report_period"] == "2024-12-31"
    assert data["has_financials"] is True
    # an auditor CHANGE surfaced by the per-context fix: current KPMG SA + prior Ernst & Young.
    # The pre-fix single-auditor extraction kept only the first DEI fact and dropped the prior firm.
    assert data["auditors"] == [
        {
            "name": "KPMG SA",
            "location": "Paris-La Defense, France",
            "firm_id": 1253,
            "icfr_attestation": True,
            "period_end": "2024-12-31",
        },
        {
            "name": "Ernst & Young et Autres",
            "location": "Courbevoie, France",
            "firm_id": 1704,
            "icfr_attestation": False,
            "period_end": "2023-12-31",
        },
    ]

    # a partial amendment: carries only the Item 19 exhibits, not the full Part I-V structure
    assert len(data["items"]) == 1
    assert _by_num(data)["19"] == {"item": "19", "part": "V", "title": "Exhibits"}

    golden("filing", "twentyf_cellectis_amendment", body)
