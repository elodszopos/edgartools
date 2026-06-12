"""Integration: /filing/{accession}/attachments list + /attachments/{sequence} content.

Attachment listings and content are served from the already-recorded SGML submission
text fixtures - no new SEC requests in this module.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_attachments_listing(client: TestClient, golden) -> None:
    # 8-K with exhibits, XBRL data files, graphics, and SEC-generated viewer files
    response = client.get("/filing/0001193125-25-004072/attachments")
    assert response.status_code == 200
    wba = response.json()
    assert wba["accession_number"] == "0001193125-25-004072"
    # the SEC-HEADER says 17 documents but the public SGML carries 16 (sequence gaps)
    assert wba["total"] == 16
    sequences = [row["sequence"] for row in wba["attachments"]]
    assert "9" not in sequences
    assert "14" not in sequences
    primary = wba["attachments"][0]
    assert primary == {
        "sequence": "1",
        "document": "d880765d8k.htm",
        "description": "8-K",
        "display_description": "8-K",
        "purpose": None,
        "document_type": "8-K",
        "size": None,
        "ixbrl": False,
        "extension": ".htm",
        "is_binary": False,
        "is_primary": True,
        "group": "document",
        "url": "https://www.sec.gov/Archives/edgar/data/1618921/000119312525004072/d880765d8k.htm",
    }
    press_release = wba["attachments"][1]
    assert press_release["sequence"] == "2"
    assert press_release["document_type"] == "EX-99.1"
    assert press_release["description"] == "EX-99.1"
    # standard exhibit description substitutes for a description that just echoes the type
    assert press_release["display_description"] == "Additional exhibit"
    assert press_release["group"] == "document"
    graphic = next(row for row in wba["attachments"] if row["sequence"] == "7")
    assert graphic["document_type"] == "GRAPHIC"
    assert graphic["is_binary"] is True
    assert graphic["group"] == "data_file"
    # SEC-viewer report file gets its purpose from the in-filing FilingSummary.xml
    r1 = next(row for row in wba["attachments"] if row["document"] == "R1.htm")
    assert r1["purpose"] == "Document and Entity Information"
    assert r1["display_description"] == "Document and Entity Information"
    golden("filing_attachments", "walgreens_8k", wba)

    # XML-native Form 4 carries exactly one document
    response = client.get("/filing/0001045810-25-000002/attachments")
    nvda = response.json()
    assert nvda["total"] == 1
    only = nvda["attachments"][0]
    assert only["sequence"] == "1"
    assert only["document"] == "wk-form4_1736377440.xml"
    assert only["document_type"] == "4"
    assert only["extension"] == ".xml"
    assert only["is_primary"] is True
    assert only["group"] == "document"
    golden("filing_attachments", "nvidia_form4", nvda)

    # 10-K: 7 filer documents then 56 data files (XBRL linkbases + R-reports + viewer assets)
    response = client.get("/filing/0001493152-25-001787/attachments")
    anixa = response.json()
    assert anixa["total"] == 63
    groups = [row["group"] for row in anixa["attachments"]]
    assert groups.count("document") == 7
    assert groups.count("data_file") == 56
    # filer supplied no descriptions; exhibits fall back to standard exhibit text
    tenk = anixa["attachments"][0]
    assert tenk["description"] is None
    assert tenk["display_description"] is None
    ex14 = anixa["attachments"][1]
    assert ex14["document_type"] == "EX-14"
    assert ex14["display_description"] == "Code of ethics"
    balance_sheet = next(row for row in anixa["attachments"] if row["document"] == "R2.htm")
    assert balance_sheet["purpose"] == "Consolidated Balance Sheets"
    xlsx = next(row for row in anixa["attachments"] if row["document"] == "Financial_Report.xlsx")
    assert xlsx["is_binary"] is True
    golden("filing_attachments", "anixa_10k", anixa)


def test_attachment_content_extraction(client: TestClient, golden) -> None:
    # exhibit text (default fmt): the WBA earnings press release
    response = client.get("/filing/0001193125-25-004072/attachments/2")
    assert response.status_code == 200
    press_text = response.json()
    assert press_text["sequence"] == "2"
    assert press_text["document"] == "d880765dex991.htm"
    assert press_text["fmt"] == "text"
    assert press_text["content"].startswith("Exhibit 99.1\nWalgreens Boots Alliance Reports Fiscal 2025 First Quarter Results")
    assert "Maintaining Full Year Adjusted EPS Guidance" in press_text["content"]
    golden("filing_attachment_content", "walgreens_ex991_text", press_text)

    # markdown of the same exhibit keeps table syntax
    response = client.get("/filing/0001193125-25-004072/attachments/2", params={"fmt": "markdown"})
    press_md = response.json()
    assert press_md["fmt"] == "markdown"
    assert press_md["content"].startswith("Exhibit 99.1\n\nWalgreens Boots Alliance Reports")
    assert "| • |" in press_md["content"]

    # raw passthrough of an XML primary document
    response = client.get("/filing/0001045810-25-000002/attachments/1", params={"fmt": "raw"})
    form4_raw = response.json()
    assert form4_raw["fmt"] == "raw"
    assert form4_raw["content"].startswith('<?xml version="1.0"?>\n<ownershipDocument>')
    assert "<rptOwnerCik>0001347842</rptOwnerCik>" in form4_raw["content"]
    golden("filing_attachment_content", "nvidia_form4_raw", form4_raw)

    # text of an XML document is the same passthrough; markdown yields null (not HTML)
    response = client.get("/filing/0001045810-25-000002/attachments/1", params={"fmt": "text"})
    assert response.json()["content"] == form4_raw["content"]
    response = client.get("/filing/0001045810-25-000002/attachments/1", params={"fmt": "markdown"})
    assert response.json()["content"] is None

    # SEC-viewer report (R2.htm) renders its statement table from the in-filing FilingSummary
    response = client.get("/filing/0001493152-25-001787/attachments/15")
    r2 = response.json()
    assert r2["document"] == "R2.htm"
    assert "Consolidated Balance Sheets - USD ($)" in r2["content"]
    assert "Oct. 31, 2024" in r2["content"]
    golden("filing_attachment_content", "anixa_r2_balance_sheet_text", r2)


def test_attachment_content_silence_checks(client: TestClient) -> None:
    # binary attachment: raw is a 422 pointing at the download url, text is null content
    response = client.get("/filing/0001193125-25-004072/attachments/7", params={"fmt": "raw"})
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "binary attachment has no JSON content; fetch https://www.sec.gov/Archives/edgar/data/1618921/000119312525004072/g880765g0110030245647.jpg"
    )
    response = client.get("/filing/0001193125-25-004072/attachments/7", params={"fmt": "text"})
    assert response.status_code == 200
    assert response.json()["content"] is None

    # missing sequence names both the sequence and the accession
    response = client.get("/filing/0001493152-25-001787/attachments/99")
    assert response.status_code == 404
    assert response.json()["detail"] == "no attachment with sequence 99 in 0001493152-25-001787"


def test_attachment_param_validation(client: TestClient) -> None:
    response = client.get("/filing/0001193125-25-004072/attachments/abc")
    assert response.status_code == 422
    response = client.get("/filing/0001193125-25-004072/attachments/2", params={"fmt": "html"})
    assert response.status_code == 422
