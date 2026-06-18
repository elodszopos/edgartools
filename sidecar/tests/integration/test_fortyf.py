"""Integration: /filing/{accession} envelope with typed Form 40-F `data` (P4).

One `FortyF` object backs 40-F and 40-F/A -> one kind (`form40f`); `form` is the variant. The 40-F
is the Canadian MJDS wrapper around the AIF + MD&A. The AIF exhibit is downloaded (one SEC request)
to extract NI 51-102 section headings and parsed section text (business, risk_factors, etc.).
Raw HTML/text blobs and MD&A live at /content + /attachments. Accessions span:

  magna    Canada FY 40-F: Deloitte auditor tagged in the wrapper iXBRL, full AIF sections
  ballard  40-F/A: is_amendment True; the amendment wrapper tags no auditor -> auditors empty
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_MAGNA = "0001193125-25-066935"
_BALLARD_A = "0001453015-25-000007"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "FortyF"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form40f"
    return body


def test_fortyf_magna_canada_mjds(client: TestClient, golden) -> None:
    body = _data(client, _MAGNA)
    data = body["data"]
    assert body["company"] == "MAGNA INTERNATIONAL INC"
    assert body["form"] == "40-F"
    assert data["is_amendment"] is False
    assert data["report_period"] == "2024-12-31"
    assert data["has_financials"] is True
    # the wrapper iXBRL tags the auditor; the AIF itself is a separate exhibit, never fetched here
    assert data["auditors"] == [
        {
            "name": "Deloitte LLP",
            "location": "Toronto, Canada",
            "firm_id": 1208,
            "icfr_attestation": True,
            "period_end": "2024-12-31",
        }
    ]
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert data["business"] is not None
    assert data["risk_factors"] is not None

    golden("filing", "fortyf_magna", body)


def test_fortyf_ballard_amendment(client: TestClient, golden) -> None:
    body = _data(client, _BALLARD_A)
    data = body["data"]
    assert body["company"] == "Ballard Power Systems Inc."
    assert body["form"] == "40-F/A"
    assert data["is_amendment"] is True
    assert data["report_period"] == "2024-12-31"
    assert data["has_financials"] is True
    # the amendment wrapper carries no DEI auditor facts -> empty list (no auditor tagged, not synthesized)
    assert data["auditors"] == []
    golden("filing", "fortyf_ballard_amendment", body)
