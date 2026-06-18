"""Integration: /filing/{accession} envelope with typed SC 13D `data` (P4 beneficial-ownership).

A 13D is the activist (control-intent) 5%+ schedule. `data` carries the cover-page identities
(issuer, security, the joint reporting persons with their voting/dispositive splits) plus the
seven narrative items - Item 4 (purpose of transaction) is the activist signal. Accessions span
the structured/degraded matrix:

  composecure        base 13D, 9-filer group (Platinum Equity), CIKs present, full Item 4 narrative
  trian_wendys       13D/A amendment: is_amendment True, restated Item 4 only (Item 2 left null)
  ekco_legacy        pre-mandate 1995 HTML-only: has_structured_data False, no persons/signatures,
                     issuer name recovered from the header, totals null

(The modern structured-XML mandate is 2024-12-18; the 1995 filing predates it, exercising the
from_header degraded path that the post-mandate filings never hit.)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_COMPOSECURE = "0001493152-26-002882"
_TRIAN_WENDYS = "0001193125-26-056159"
_EKCO_LEGACY = "0000950135-95-000828"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Schedule13D"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "sc13d"
    return body


def test_schedule13d_composecure_group(client: TestClient, golden) -> None:
    body = _data(client, _COMPOSECURE)
    data = body["data"]
    assert body["company"] == "CompoSecure, Inc."
    assert body["form"] == "SCHEDULE 13D"
    assert data["is_amendment"] is False
    assert data["amendment_number"] is None
    assert data["has_structured_data"] is True
    assert data["previously_filed"] is False
    assert data["event_date"] == "01/12/2026"
    # totals: max() across the nine overlapping group owners (all report the same 52.8M block)
    assert data["total_shares"] == 52829757
    assert data["total_percent"] == 18.3

    issuer = data["issuer"]
    assert issuer["name"] == "CompoSecure, Inc."
    assert issuer["cik"] == "0001823144"
    assert issuer["cusip"] == "20459V105"
    assert issuer["address"]["city"] == "Somerset"
    assert issuer["address"]["state_or_country"] == "NJ"
    assert issuer["address"]["zipcode"] == "08873"
    assert data["security"]["title"] == "Class A Common Stock, par value $0.0001 per share"
    assert data["security"]["cusip"] == "20459V105"

    # nine-filer Platinum Equity group; the lead filer holds the block via shared power
    assert len(data["reporting_persons"]) == 9
    lead = data["reporting_persons"][0]
    assert lead["name"] == "Platinum Equity, LLC"
    assert lead["cik"] == "0001228754"
    assert lead["type_of_reporting_person"] == "OO"
    assert lead["citizenship"] == "DE"
    assert lead["percent_of_class"] == 18.3
    assert lead["aggregate_amount"] == 52829757
    assert lead["sole_voting_power"] == 0
    assert lead["shared_voting_power"] == 52829757
    assert lead["fund_type"] == "OO"
    assert lead["no_cik"] is False

    assert data["items"]["item1_issuer_name"] == "CompoSecure, Inc."
    assert data["items"]["item4_purpose_of_transaction"].startswith("Transaction Agreement")
    assert len(data["signatures"]) == 9
    assert data["signatures"][0]["reporting_person"] == "Platinum Equity, LLC"
    assert data["signatures"][0]["signature"] == "/s/ Mary Ann Sigler"

    golden("filing", "schedule13d_composecure", body)


def test_schedule13d_trian_wendys_amendment(client: TestClient, golden) -> None:
    body = _data(client, _TRIAN_WENDYS)
    data = body["data"]
    assert body["company"] == "TRIAN FUND MANAGEMENT, L.P."
    assert body["form"] == "SCHEDULE 13D/A"
    # amendment number recovered from the structured <amendmentNo> cover-page tag (not the form suffix)
    assert data["is_amendment"] is True
    assert data["amendment_number"] == 64
    assert data["has_structured_data"] is True
    assert data["event_date"] == "02/18/2026"
    assert data["total_shares"] == 30913106
    assert data["total_percent"] == 16.24

    assert data["issuer"]["name"] == "The Wendy's Company"
    assert data["issuer"]["cik"] == "0000030697"
    assert data["issuer"]["cusip"] == "95058W100"
    assert data["security"]["title"] == "Common Stock, Par Value $.10 Per Share"

    # 12-filer Trian group; lead individuals carry shared voting + sole dispositive
    assert len(data["reporting_persons"]) == 12
    peltz = data["reporting_persons"][0]
    assert peltz["name"] == "Nelson Peltz"
    assert peltz["cik"] == "0000928265"
    assert peltz["type_of_reporting_person"] == "IN"
    assert peltz["percent_of_class"] == 16.24
    assert peltz["shared_voting_power"] == 30913106
    assert peltz["sole_dispositive_power"] == 9959519
    assert data["reporting_persons"][1]["name"] == "Peter W. May"
    assert data["reporting_persons"][1]["percent_of_class"] == 16.13

    # an /A restating only Item 4: the un-restated narrative items come back null
    assert data["items"]["item1_issuer_name"] == "The Wendy's Company"
    assert data["items"]["item2_filing_persons"] is None
    assert data["items"]["item4_purpose_of_transaction"].startswith("Item 4 is hereby amended and restated")
    assert len(data["signatures"]) == 12
    assert data["signatures"][0]["reporting_person"] == "Nelson Peltz"
    assert data["signatures"][0]["date"] == "02/18/2026"

    golden("filing", "schedule13d_trian_wendys_amendment", body)


def test_schedule13d_ekco_legacy_degraded(client: TestClient, golden) -> None:
    body = _data(client, _EKCO_LEGACY)
    data = body["data"]
    assert body["company"] == "EKCO GROUP INC /DE/"
    assert body["form"] == "SC 13D"
    # 1995 HTML-only: no structured XML, so the cover-page numerics never parse
    assert data["has_structured_data"] is False
    assert data["is_amendment"] is False
    assert data["total_shares"] is None
    assert data["total_percent"] is None
    assert data["event_date"] is None

    # only the header identity survives the degraded path; issuer cik is the raw as-filed value
    # (not zero-padded like the envelope-level cik), cusip/address never recovered
    assert data["issuer"]["name"] == "EKCO GROUP INC /DE/"
    assert data["issuer"]["cik"] == "18827"
    assert data["issuer"]["cusip"] is None
    assert data["issuer"]["address"] is None
    assert data["security"]["title"] is None

    # the structured cover-page lists are empty, not fabricated
    assert data["reporting_persons"] == []
    assert data["signatures"] == []
    assert data["items"]["item1_issuer_name"] is None

    golden("filing", "schedule13d_ekco_legacy", body)
