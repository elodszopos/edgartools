"""Integration: /filing/{accession} envelope with typed Form 6-K `data` (the P4 current-report payload).

6-K (Report of Foreign Private Issuer) has no numbered items; `data` carries the cover-page metadata
(commission file number, report month, the 20-F/40-F annual-report checkbox, the material-contained
description) plus content-exhibit refs. Two accessions contrast a fully-populated report against a
bare one:

  fiftyone_talk   report month + 20-F checkbox + commission file number + EX-99.1 press release
  anglogold       bare: no exhibits, no checked annual-report form, no press release
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_51TALK = "0001104659-26-073181"
_ANGLOGOLD = "0001973832-26-000099"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "SixK"
    assert body["form"].startswith("6-K")
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form6k"
    return body


def test_form6k_fiftyone_talk_full_cover(client: TestClient, golden) -> None:
    body = _data(client, _51TALK)
    data = body["data"]
    assert body["company"] == "51Talk Online Education Group"
    assert data["form"] == "6-K"
    assert data["date_of_report"] == "June 12, 2026"
    assert data["commission_file_number"] == "001-37790"
    assert data["report_month"] == "June 2026"
    # the issuer files annual reports on Form 20-F (the cover checkbox)
    assert data["annual_report_form"] == "20-F"
    # one EX-99.1 press release exhibit
    assert data["has_exhibits"] is True
    assert data["has_press_release"] is True
    assert [ex["document_type"] for ex in data["exhibits"]] == ["EX-99.1"]

    golden("filing", "form6k_fiftyone_talk_full_cover", body)


def test_form6k_anglogold_bare(client: TestClient, golden) -> None:
    body = _data(client, _ANGLOGOLD)
    data = body["data"]
    assert body["company"] == "AngloGold Ashanti PLC"
    assert data["commission_file_number"] == "001-41815"
    assert data["report_month"] == "June 2026"
    # no annual-report checkbox, no content exhibits, no press release
    assert data["annual_report_form"] is None
    assert data["has_exhibits"] is False
    assert data["has_press_release"] is False
    assert data["exhibits"] == []
    assert data["content_description"] is None

    golden("filing", "form6k_anglogold_bare", body)
