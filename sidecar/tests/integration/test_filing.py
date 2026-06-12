"""Integration: /filing/{accession} envelope.

One VCR test: the 2025 Q1 index download is the expensive interaction, so every
envelope scenario (single-entity, joint filers, Form 4 owner/issuer, 404) shares one
cassette via the in-session HTTP cache. The 404 case uses a 1995 accession so the
not-found scan stays in the small early-EDGAR indexes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.vcr
def test_filing_envelope_entities_header_and_missing(client: TestClient, golden) -> None:
    # single-entity 8-K with three items (Walgreens Q1 earnings day)
    response = client.get("/filing/0001193125-25-004072")
    assert response.status_code == 200
    wba = response.json()
    assert wba["accession_number"] == "0001193125-25-004072"
    assert wba["form"] == "8-K"
    assert wba["cik"] == "0001618921"
    assert wba["company"] == "Walgreens Boots Alliance, Inc."
    assert wba["filing_date"] == "2025-01-10"
    assert wba["is_multi_entity"] is False
    assert wba["entities"] == [
        {
            "cik": "0001618921",
            "company": "Walgreens Boots Alliance, Inc.",
            "form": "8-K",
            "filing_date": "2025-01-10",
        }
    ]
    header = wba["header"]
    # SEC-HEADER says 07:15:33 (Eastern, EST in January) -> UTC
    assert header["acceptance_datetime"] == "2025-01-10T12:15:33Z"
    assert header["filing_date"] == "2025-01-10"
    assert header["period_of_report"] == "2025-01-10"
    assert header["date_as_of_change"] == "2025-01-10"
    assert header["document_count"] == 17
    assert header["items"] == [
        "Results of Operations and Financial Condition",
        "Regulation FD Disclosure",
        "Financial Statements and Exhibits",
    ]
    assert len(header["filers"]) == 1
    assert header["reporting_owners"] == []
    assert header["issuer"] is None
    assert header["subject_companies"] == []
    assert wba["primary_documents"][0]["document"] == "d880765d8k.htm"
    assert wba["obj_type"] == "EightK"
    assert wba["data"] is None
    assert wba["homepage_url"].endswith("/0001193125-25-004072-index.html")
    assert wba["text_url"].endswith("/0001193125-25-004072.txt")
    golden("filing", "walgreens_8k", wba)

    # joint filers: Carnival Corp + Carnival plc share one 8-K accession
    response = client.get("/filing/0001104659-25-002319")
    assert response.status_code == 200
    ccl = response.json()
    assert ccl["cik"] == "0000815097"
    assert ccl["company"] == "CARNIVAL CORP"
    assert ccl["is_multi_entity"] is True
    assert ccl["entities"] == [
        {"cik": "0000815097", "company": "CARNIVAL CORP", "form": "8-K", "filing_date": "2025-01-10"},
        {"cik": "0001125259", "company": "CARNIVAL PLC", "form": "8-K", "filing_date": "2025-01-10"},
    ]
    header = ccl["header"]
    assert header["acceptance_datetime"] == "2025-01-10T14:00:22Z"
    assert header["period_of_report"] == "2025-01-09"
    assert header["document_count"] == 15
    corp, plc = header["filers"]
    assert corp["company"] == {
        "name": "CARNIVAL CORP",
        "cik": "0000815097",
        "sic": "WATER TRANSPORTATION [4400]",
        "irs_number": "591562976",
        "state_of_incorporation": "R1",  # SEC country code for Panama
        "fiscal_year_end": "1130",
    }
    assert corp["filing_values"] == {
        "form": "8-K",
        "file_number": "001-09610",
        "sec_act": "1934 Act",
        "film_number": "25520684",
    }
    assert corp["business_address"] == {
        "street1": "3655 NW 87TH AVE",
        "street2": "PO BOX 1347",
        "city": "MIAMI",
        "state_or_country": "FL",
        "zipcode": "33178-2428",
    }
    assert corp["former_names"] == [{"name": "CARNIVAL CRUISE LINES INC", "date_of_change": "1992-07-03"}]
    assert plc["company"]["name"] == "CARNIVAL PLC"
    assert plc["company"]["cik"] == "0001125259"
    assert plc["filing_values"]["file_number"] == "001-15136"
    assert plc["former_names"] == [{"name": "P&O PRINCESS CRUISES PLC", "date_of_change": "2000-09-29"}]
    golden("filing", "carnival_joint_8k", ccl)

    # Form 4 exercises the issuer + reporting-owner header branches (NVIDIA insider)
    response = client.get("/filing/0001045810-25-000002")
    assert response.status_code == 200
    nvda = response.json()
    assert nvda["form"] == "4"
    assert nvda["cik"] == "0001045810"
    assert nvda["is_multi_entity"] is True
    assert nvda["entities"] == [
        {"cik": "0001045810", "company": "NVIDIA CORP", "form": "4", "filing_date": "2025-01-08"},
        {"cik": "0001347842", "company": "Puri Ajay K", "form": "4", "filing_date": "2025-01-08"},
    ]
    header = nvda["header"]
    assert header["acceptance_datetime"] == "2025-01-08T23:04:06Z"
    assert header["period_of_report"] == "2025-01-06"
    assert header["document_count"] == 1
    assert header["filers"] == []
    owner = header["reporting_owners"][0]
    # raw conformed name as filed ("Last First Middle") - no per-owner SEC lookup
    assert owner["name"] == "Puri Ajay K"
    assert owner["cik"] == "0001347842"
    assert owner["company"] is None
    assert owner["filing_values"] == {
        "form": "4",
        "file_number": "000-23985",
        "sec_act": "1934 Act",
        "film_number": "25519543",
    }
    assert owner["business_address"] is None
    assert owner["mailing_address"] == {
        "street1": "2788 SAN TOMAS EXPRESSWAY",
        "street2": None,
        "city": "SANTA CLARA",
        "state_or_country": "CA",
        "zipcode": "95051",
    }
    issuer = header["issuer"]
    assert issuer["company"]["name"] == "NVIDIA CORP"
    assert issuer["company"]["cik"] == "0001045810"
    assert issuer["company"]["state_of_incorporation"] == "DE"
    assert issuer["company"]["fiscal_year_end"] == "0126"
    doc = nvda["primary_documents"][0]
    assert doc["document"] == "wk-form4_1736377440.xml"
    assert doc["document_type"] == "4"
    assert nvda["obj_type"] == "Form4"
    golden("filing", "nvidia_form4", nvda)

    # nonexistent accession -> 404 with the accession named (silence check)
    response = client.get("/filing/0000000000-95-654321")
    assert response.status_code == 404
    assert "0000000000-95-654321" in response.json()["detail"]


def test_filing_accession_format_validation(client: TestClient) -> None:
    response = client.get("/filing/not-an-accession")
    assert response.status_code == 422
