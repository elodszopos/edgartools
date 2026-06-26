"""Integration (U58): the EFFECT filing -> kind=effect.

An EFFECT filing is the SEC's terminal notification that a registration statement has been
declared effective. Tiny form: effective_date, filer identity, source form type/accession.

  aim         EFFECT for an S-1 registration, source_accession_no absent (typical -- most EFFECT
              filings carry only the file number, not the source accession)
  toyo        EFFECT for a POS AM (post-effective amendment), source_accession_no populated
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_AIM = "9999999995-26-002094"  # EFFECT, AIM ImmunoTech -> S-1
_TOYO = "9999999995-26-002085"  # EFFECT, TOYO Co -> POS AM (source accession populated)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _effect(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Effect"
    assert body["data"] is not None
    assert body["data"]["kind"] == "effect"
    return body


def test_effect_s1_registration(client: TestClient, golden) -> None:
    body = _effect(client, _AIM)
    data = body["data"]
    assert data["form"] == "EFFECT"
    assert data["cik"] == "0000946644"
    assert data["entity"] == "AIM ImmunoTech Inc."
    assert data["submission_type"] == "EFFECT"
    assert data["is_live"] is True
    assert data["schema_version"] == "X0101"
    assert data["effective_date"] == "2026-06-23"
    assert data["source_submission_type"] == "S-1"
    assert data["source_accession_no"] is None
    assert data["source_file_number"] == "333-296871"
    golden("filing", "effect_aim_s1", body)


def test_effect_pos_am_with_source_accession(client: TestClient, golden) -> None:
    body = _effect(client, _TOYO)
    data = body["data"]
    assert data["form"] == "EFFECT"
    assert data["entity"] == "TOYO Co., Ltd"
    assert data["is_live"] is True
    assert data["source_submission_type"] == "POS AM"
    assert data["source_accession_no"] == "0001213900-26-070425"
    assert data["source_file_number"] is not None
    golden("filing", "effect_toyo_pos_am", body)
