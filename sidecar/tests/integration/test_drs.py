"""Integration (U53b): the DRS / DRS/A draft-registration family over the one
`DraftRegistrationStatement` -> kind=drs.

A DRS is a confidential draft registration; EDGAR only labels it "DRS"/"DRS/A", and the underlying
form is detected from the cover text. edgar builds a delegated `underlying_object` only for S-1/F-1
(-> RegistrationS1) and S-3 (-> RegistrationS3); S-4/F-4/20-F/Form 10/Unknown carry None. The DRS
wire payload wraps that embedded U53a/U54 model (a nested discriminated union on its own `kind`).

Five fixtures pin the matrix:

  verde      DRS    draft S-1  -> underlying_object = registration_s1 (domestic, clean cover w/ EIN)
  weride     DRS    draft F-1  -> underlying_object = registration_s1 (foreign / Cayman)
  biontech   DRS    draft F-4  -> underlying_object = None (edgar builds no delegate for S-4/F-4)
  blackrock  DRS/A  draft S-1  -> amendment (No. 1), underlying_object = registration_s1
  aoje       DRS/A  draft F-1  -> amendment (No. 3), underlying_object = registration_s1

Drafts predate the fee filing, so the embedded fee_table is None or an empty shell (the fee table
itself is exercised by U53a/U54); here the asserts focus on the DRS wrapping and the delegation.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_VERDE = "0001640334-25-001090"  # DRS draft S-1, Verde Resources, Inc.
_WERIDE = "0001104659-25-063686"  # DRS draft F-1, WeRide Inc. (Cayman)
_BIONTECH = "0000950123-25-006152"  # DRS draft F-4, BioNTech SE (no delegate built)
_BLACKROCK = "0001628279-25-000398"  # DRS/A draft S-1 amendment No. 1, Black Rock Coffee Bar
_AOJE = "0001641172-25-016922"  # DRS/A draft F-1 amendment No. 3, AOJE Inc. (Cayman)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _drs(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "DraftRegistrationStatement"  # DRS and DRS/A both -> this object
    assert body["data"] is not None
    assert body["data"]["kind"] == "drs"
    return body


def test_drs_draft_s1_wraps_registration_s1(client: TestClient, golden) -> None:
    body = _drs(client, _VERDE)
    data = body["data"]
    assert data["form"] == "DRS"
    assert data["underlying_form"] == "S-1"
    assert data["is_amendment"] is False
    assert data["amendment_number"] is None
    assert data["registration_number"] == "377-08158"
    assert data["company"] == "VERDE RESOURCES, INC."

    # the embedded U53a payload, reused verbatim and discriminated on its own kind
    uo = data["underlying_object"]
    assert uo is not None
    assert uo["kind"] == "registration_s1"
    assert uo["offering_type"] == "unknown"
    assert uo["cover_page"]["state_of_incorporation"] == "Nevada"
    assert uo["cover_page"]["ein"] == "32-0457838"
    assert uo["cover_page"]["confidence"] == "high"
    golden("filing", "drs_verde_s1", body)


def test_drs_draft_f1_foreign(client: TestClient, golden) -> None:
    body = _drs(client, _WERIDE)
    data = body["data"]
    assert data["form"] == "DRS"
    assert data["underlying_form"] == "F-1"
    assert data["is_amendment"] is False
    assert data["registration_number"] == "377-08150"
    assert data["company"] == "WeRide Inc."

    uo = data["underlying_object"]
    assert uo is not None
    assert uo["kind"] == "registration_s1"
    assert uo["cover_page"]["state_of_incorporation"] == "Cayman Islands"
    assert uo["cover_page"]["confidence"] == "medium"
    golden("filing", "drs_weride_f1", body)


def test_drs_draft_f4_no_delegate(client: TestClient, golden) -> None:
    body = _drs(client, _BIONTECH)
    data = body["data"]
    assert data["form"] == "DRS"
    assert data["underlying_form"] == "F-4"  # detected from cover; edgar builds no delegate for F-4
    assert data["is_amendment"] is False
    assert data["registration_number"] == "377-08160"
    assert data["company"] == "BioNTech SE"
    # no RegistrationS1/S3 is constructed for an S-4/F-4 underlying -> the wrapper still parses
    assert data["underlying_object"] is None
    golden("filing", "drs_biontech_f4_no_underlying", body)


def test_drsa_amendment_s1(client: TestClient, golden) -> None:
    body = _drs(client, _BLACKROCK)
    data = body["data"]
    assert data["form"] == "DRS/A"
    assert data["underlying_form"] == "S-1"
    assert data["is_amendment"] is True
    assert data["amendment_number"] == 1  # "Amendment No. 1" parsed from the cover
    assert data["registration_number"] == "377-08026"
    assert data["company"] == "Black Rock Coffee Bar, Inc."

    uo = data["underlying_object"]
    assert uo is not None
    assert uo["kind"] == "registration_s1"
    assert uo["offering_type"] == "ipo"
    assert uo["cover_page"]["state_of_incorporation"] == "Texas"
    assert uo["cover_page"]["ein"] == "33-5053729"
    golden("filing", "drs_blackrock_s1a_amendment", body)


def test_drsa_amendment_f1_higher_number(client: TestClient, golden) -> None:
    body = _drs(client, _AOJE)
    data = body["data"]
    assert data["form"] == "DRS/A"
    assert data["underlying_form"] == "F-1"
    assert data["is_amendment"] is True
    assert data["amendment_number"] == 3  # "Amendment No. 3" -> proves multi-digit amendment parsing
    assert data["registration_number"] == "377-07667"
    assert data["company"] == "AOJE INC."

    uo = data["underlying_object"]
    assert uo is not None
    assert uo["kind"] == "registration_s1"
    assert uo["offering_type"] == "ipo"
    # edgar's cover extractor leaves embedded whitespace in this issuer's state; mirror it faithfully
    assert uo["cover_page"]["state_of_incorporation"].startswith("Cayman")
    golden("filing", "drs_aoje_f1a_amendment", body)
