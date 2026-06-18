"""Integration: /filing/{accession} envelope with typed SC 13G `data` (P4 beneficial-ownership).

A 13G is the passive (no control-intent) 5%+ schedule - institutional managers and exempt
investors. `data` shares the cover-page shape with 13D but carries the flag-heavy 13G items
(mostly not-applicable booleans + the Item 4 ownership block) plus rule_designation and the
always-true is_passive_investor. Accessions span the structured/degraded matrix:

  mackay_nine_energy base 13G, 2 institutional filers (IA/IV) sharing the block, member_of_group 'b'
  fmr_amendment      13G/A: is_amendment True, sole-power holder (FMR), decimal item4 amount string
  bankamerica_legacy pre-mandate 1995 HTML-only: has_structured_data False, no persons, totals null,
                     every item flag defaults True, issuer name recovered from the header

(The 1995 filing predates the 2024-12-18 structured-XML mandate, exercising the from_header
degraded path; is_passive_investor stays True even there - it is intrinsic to the 13G form.)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_MACKAY = "0001085146-26-000289"
_FMR_AMENDMENT = "0000315066-26-001210"
_BANKAMERICA_LEGACY = "0000898430-95-000466"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Schedule13G"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "sc13g"
    return body


def test_schedule13g_mackay_institutional(client: TestClient, golden) -> None:
    body = _data(client, _MACKAY)
    data = body["data"]
    assert body["company"] == "MACKAY SHIELDS LLC"
    assert body["form"] == "SCHEDULE 13G"
    assert data["is_amendment"] is False
    assert data["amendment_number"] is None
    assert data["has_structured_data"] is True
    assert data["is_passive_investor"] is True
    assert data["rule_designation"] == "Rule 13d-1(b)"
    assert data["event_date"] == "03/05/2026"
    assert data["total_shares"] == 1662134
    assert data["total_percent"] == 11.91

    # issuer is the subject company (Nine Energy), distinct from the filer (MacKay Shields)
    assert data["issuer"]["name"] == "Nine Energy Service, Inc."
    assert data["issuer"]["cik"] == "0001532286"
    assert data["issuer"]["cusip"] == "65441V200"
    assert data["security"]["title"] == "Common Stock"

    # two institutional filers; 13G cover pages carry no person CIK -> null, member_of_group 'b'
    assert len(data["reporting_persons"]) == 2
    adviser = data["reporting_persons"][0]
    assert adviser["name"] == "MacKay Shields LLC"
    assert adviser["cik"] is None
    assert adviser["type_of_reporting_person"] == "IA"
    assert adviser["citizenship"] == "DE"
    assert adviser["percent_of_class"] == 11.91
    assert adviser["aggregate_amount"] == 1662134
    assert adviser["sole_voting_power"] == 0
    assert adviser["shared_voting_power"] == 1662134
    assert adviser["member_of_group"] == "b"
    assert adviser["no_cik"] is False
    fund = data["reporting_persons"][1]
    assert fund["name"] == "NYLI MacKay High Yield Corporate Bond Fund"
    assert fund["type_of_reporting_person"] == "IV"
    assert fund["member_of_group"] == "b"

    # 13G items: the not-applicable flags carry real mixed state
    items = data["items"]
    assert items["item1_issuer_name"] == "Nine Energy Service, Inc."
    assert items["item3_not_applicable"] is False
    assert items["item5_not_applicable"] is True
    assert items["item7_not_applicable"] is True
    assert items["item4_amount_beneficially_owned"].startswith("MacKay Shields LLC - 1,662,134")
    assert items["item4_percent_of_class"] == "21.98"
    assert items["item10_certification"].startswith("By signing below I certify")

    assert len(data["signatures"]) == 2
    assert data["signatures"][0]["reporting_person"] == "MacKay Shields LLC"
    assert data["signatures"][0]["signature"] == "Chris Fitzgerald"
    assert data["signatures"][0]["title"] == "Chief Compliance Officer"

    golden("filing", "schedule13g_mackay_nine_energy", body)


def test_schedule13g_fmr_amendment(client: TestClient, golden) -> None:
    body = _data(client, _FMR_AMENDMENT)
    data = body["data"]
    assert body["company"] == "FMR LLC"
    assert body["form"] == "SCHEDULE 13G/A"
    assert data["is_amendment"] is True
    assert data["amendment_number"] == 1  # recovered from the structured <amendmentNo> cover-page tag
    assert data["has_structured_data"] is True
    assert data["is_passive_investor"] is True
    assert data["rule_designation"] == "Rule 13d-1(b)"
    assert data["event_date"] == "03/31/2026"
    assert data["total_shares"] == 39551932
    assert data["total_percent"] == 13.7

    assert data["issuer"]["name"] == "GPGI INC"
    assert data["issuer"]["cik"] == "0001823144"
    assert data["issuer"]["cusip"] == "20459V105"
    assert data["security"]["title"] == "CLASS A COMMON STOCK"

    # FMR holds sole power (vs MacKay's all-shared); Johnson mirrors the deemed-ownership block
    assert len(data["reporting_persons"]) == 2
    fmr = data["reporting_persons"][0]
    assert fmr["name"] == "FMR LLC"
    assert fmr["cik"] is None
    assert fmr["type_of_reporting_person"] == "HC"
    assert fmr["sole_voting_power"] == 36647259
    assert fmr["shared_voting_power"] == 0
    assert fmr["sole_dispositive_power"] == 39551932
    assert fmr["member_of_group"] is None
    assert data["reporting_persons"][1]["name"] == "Abigail P. Johnson"
    assert data["reporting_persons"][1]["type_of_reporting_person"] == "IN"

    items = data["items"]
    assert items["item1_issuer_name"] == "GPGI INC"
    # item4 amount filed as a decimal string; passed through verbatim (not coerced to int)
    assert items["item4_amount_beneficially_owned"] == "39551932.38"
    assert items["item4_percent_of_class"] == "13.7"
    # item7 applicable here (vs MacKay's True) - exercises the flag both ways across the 13G set
    assert items["item7_not_applicable"] is False

    golden("filing", "schedule13g_fmr_amendment", body)


def test_schedule13g_bankamerica_legacy_degraded(client: TestClient, golden) -> None:
    body = _data(client, _BANKAMERICA_LEGACY)
    data = body["data"]
    assert body["company"] == "BANKAMERICA CORP"
    assert body["form"] == "SC 13G"
    # 1995 HTML-only degraded path: no structured numerics
    assert data["has_structured_data"] is False
    assert data["is_amendment"] is False
    assert data["total_shares"] is None
    assert data["total_percent"] is None
    assert data["event_date"] is None
    assert data["rule_designation"] is None
    # is_passive_investor is intrinsic to the 13G form, true even without structured data
    assert data["is_passive_investor"] is True

    assert data["issuer"]["name"] == "BANKAMERICA CORP"
    assert data["issuer"]["cik"] == "9672"
    assert data["issuer"]["cusip"] is None
    assert data["reporting_persons"] == []
    assert data["signatures"] == []

    # degraded items: every not-applicable flag defaults True, narrative fields null
    items = data["items"]
    assert items["item1_issuer_name"] is None
    assert items["item3_not_applicable"] is True
    assert items["item5_not_applicable"] is True
    assert items["item7_not_applicable"] is True
    assert items["item9_not_applicable"] is True

    golden("filing", "schedule13g_bankamerica_legacy", body)
