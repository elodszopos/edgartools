"""Integration: /filing/{accession} envelope + /content + /sections.

Every request resolves to a URL-keyed fixture; the 2025 Q1 index download is the
expensive one. The 404 case uses a 1995 accession so the not-found scan stays in the
small early-EDGAR indexes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


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
    # U43: an 8-K envelope now carries typed current-report data (obj_type + data populate together)
    assert wba["obj_type"] == "CurrentReport"
    wba_data = wba["data"]
    assert wba_data["kind"] == "form8k"
    assert wba_data["form"] == "8-K"
    assert wba_data["content_type"] == "earnings"
    assert wba_data["date_of_report"] == "January 10, 2025"
    assert [item["item"] for item in wba_data["items"]] == ["2.02", "7.01", "9.01"]
    assert wba_data["has_press_release"] is True
    assert wba_data["has_earnings"] is True
    # EX-99.1 press release + the financial-report EXCEL workbook (EXCEL is not in the skip set)
    assert [ex["document_type"] for ex in wba_data["exhibits"]] == ["EX-99.1", "EXCEL"]
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
        # canonical Address shape: the SGML header parse never carries the description
        "state_or_country_description": None,
        "zipcode": "33178-2428",
    }
    assert corp["former_names"] == [{"name": "CARNIVAL CRUISE LINES INC", "date_of_change": "1992-07-03"}]
    assert plc["company"]["name"] == "CARNIVAL PLC"
    assert plc["company"]["cik"] == "0001125259"
    assert plc["filing_values"]["file_number"] == "001-15136"
    assert plc["former_names"] == [{"name": "P&O PRINCESS CRUISES PLC", "date_of_change": "2000-09-29"}]
    # U43: the joint 8-K carries typed current-report data too (single Item 5.02, no press release)
    assert ccl["obj_type"] == "CurrentReport"
    ccl_data = ccl["data"]
    assert ccl_data["kind"] == "form8k"
    assert ccl_data["content_type"] == "director_change"
    assert ccl_data["date_of_report"] == "January 09, 2025"
    assert [item["item"] for item in ccl_data["items"]] == ["5.02"]
    assert ccl_data["has_press_release"] is False
    assert ccl_data["has_earnings"] is False
    assert [ex["document_type"] for ex in ccl_data["exhibits"]] == ["EXCEL"]
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
        "state_or_country_description": None,
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
    # U40: a Form 4 envelope now carries typed ownership data (obj_type + data populate together)
    assert nvda["obj_type"] == "Form4"
    assert nvda["data"]["kind"] == "ownership"
    assert nvda["data"]["form"] == "4"
    assert nvda["data"]["issuer"]["name"] == "NVIDIA CORP"
    assert nvda["data"]["reporting_owners"], "the Form 4 names at least one reporting owner"
    golden("filing", "nvidia_form4", nvda)

    # nonexistent accession -> 404 with the accession named (silence check)
    response = client.get("/filing/0000000000-95-654321")
    assert response.status_code == 404
    assert "0000000000-95-654321" in response.json()["detail"]


def test_filing_content_formats(client: TestClient, golden) -> None:
    # markdown (default): whole-document render of the primary HTML
    response = client.get("/filing/0001193125-25-004072/content")
    assert response.status_code == 200
    md = response.json()
    assert md["accession_number"] == "0001193125-25-004072"
    assert md["fmt"] == "markdown"
    assert md["content"].startswith("UNITED STATES SECURITIES AND EXCHANGE COMMISSION Washington, D.C. 20549 FORM 8-K")
    golden("filing_content", "walgreens_8k_markdown", md)

    # text view of the same document
    response = client.get("/filing/0001193125-25-004072/content", params={"fmt": "text"})
    text = response.json()
    assert text["fmt"] == "text"
    assert "Results of Operations and Financial Condition" in text["content"]
    assert "Walgreens Boots Alliance, Inc." in text["content"]

    # raw html view
    response = client.get("/filing/0001193125-25-004072/content", params={"fmt": "html"})
    html = response.json()
    assert html["fmt"] == "html"
    assert "SECURITIES AND EXCHANGE COMMISSION" in html["content"]
    assert "<" in html["content"]

    # XML-native Form 4 renders through the ownership object to html/text/markdown
    response = client.get("/filing/0001045810-25-000002/content", params={"fmt": "text"})
    nvda = response.json()
    assert nvda["fmt"] == "text"
    assert "FORM 4" in nvda["content"]
    assert "Puri" in nvda["content"]
    golden("filing_content", "nvidia_form4_text", nvda)

    # page_breaks=true with markdown is valid and returns content
    response = client.get("/filing/0001193125-25-004072/content", params={"fmt": "markdown", "page_breaks": "true"})
    assert response.status_code == 200
    pb = response.json()
    assert pb["fmt"] == "markdown"
    assert pb["content"] is not None
    assert len(pb["content"]) > 0

    # page_breaks only makes sense for markdown
    response = client.get("/filing/0001193125-25-004072/content", params={"fmt": "text", "page_breaks": "true"})
    assert response.status_code == 422

    # unknown fmt rejected
    response = client.get("/filing/0001193125-25-004072/content", params={"fmt": "pdf"})
    assert response.status_code == 422


def test_filing_sections_detection(client: TestClient, golden) -> None:
    # 10-K with TOC-detected sections across Parts I-IV (Anixa Biosciences FY2024)
    response = client.get("/filing/0001493152-25-001787/sections")
    assert response.status_code == 200
    tenk = response.json()
    assert tenk["fmt"] == "text"
    assert tenk["total"] == 22
    first = tenk["sections"][0]
    assert first["name"] == "part_i_item_1"
    assert first["part"] == "I"
    assert first["item"] == "1"
    assert first["detection_method"] == "toc"
    assert first["confidence"] == 0.95
    assert first["content"].startswith("Item 1. Business\n\nOverview\n\nAnixa Biosciences, Inc. is a biotechnology")
    names = [s["name"] for s in tenk["sections"]]
    assert names[-1] == "part_iv_item_16"
    assert "part_ii_item_7" in names  # MD&A present
    golden("filing_sections", "anixa_10k_text", tenk)

    # markdown variant preserves table/list syntax per section
    response = client.get(
        "/filing/0001493152-25-001787/sections",
        params={"fmt": "markdown"},
    )
    tenk_md = response.json()
    assert tenk_md["fmt"] == "markdown"
    assert tenk_md["total"] == 22
    assert tenk_md["sections"][0]["content"].startswith("<u>Business</u>")

    # 8-K items detected by pattern
    response = client.get("/filing/0001193125-25-004072/sections")
    eightk = response.json()
    assert eightk["total"] == 3
    assert [s["name"] for s in eightk["sections"]] == ["item_202", "item_701", "item_901"]
    item202 = eightk["sections"][0]
    assert item202["title"] == "Item 2.02 - Results of Operations"
    assert item202["item"] == "202"
    assert item202["part"] is None
    assert item202["detection_method"] == "pattern"
    assert item202["confidence"] == 0.7
    # the space after "Item" below is U+2009 (thin space) as rendered from the source html
    assert item202["content"].startswith("Item 2.02. Results of Operations and Financial Condition.")
    golden("filing_sections", "walgreens_8k_text", eightk)

    # rendered Form 4 has no section structure - empty, not an error
    response = client.get("/filing/0001045810-25-000002/sections")
    form4 = response.json()
    assert form4["total"] == 0
    assert form4["sections"] == []


def test_filing_envelope_data_null(client: TestClient, golden) -> None:
    # CORRESP is permanently envelope-only (not in _DATA_BUILDERS) -> data=null, obj_type=null
    response = client.get("/filing/0001104659-22-119482")
    assert response.status_code == 200
    corresp = response.json()
    assert corresp["accession_number"] == "0001104659-22-119482"
    assert corresp["form"] == "CORRESP"
    assert corresp["data"] is None
    assert corresp["obj_type"] is None
    assert corresp["header"] is not None
    assert corresp["entities"] != []
    golden("filing", "corresp_data_null", corresp)


def test_filing_accession_format_validation(client: TestClient) -> None:
    response = client.get("/filing/not-an-accession")
    assert response.status_code == 422
    response = client.get("/filing/0001193125-25-004072/sections", params={"fmt": "html"})
    assert response.status_code == 422
