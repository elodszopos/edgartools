"""Integration: /company/{id} profile + /company/{id}/submissions history.

All VCR tests share company_p3_fixtures.yaml. The profile is built from the SEC
submissions store JSON only (data.sec.gov/submissions/CIK##########.json); the
submissions endpoint additionally loads pagination files for long filers. Ground
truth verified by hand against the recorded SEC responses (2026-06-12).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def vcr_cassette_name():
    return "company_p3_fixtures"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.vcr
def test_company_profile_operating_company(client: TestClient, golden) -> None:
    # ticker resolution path: AAPL -> CIK 320193 via the SEC company tickers map
    response = client.get("/company/AAPL")
    assert response.status_code == 200
    aapl = response.json()
    assert aapl == {
        "cik": "0000320193",
        "name": "Apple Inc.",
        "display_name": "Apple Inc.",
        "entity_type": "operating",
        "tickers": ["AAPL"],
        "exchanges": ["Nasdaq"],
        "sic": "3571",
        "sic_description": "Electronic Computers",
        "category": "Large accelerated filer",
        "filer_status": "Large accelerated filer",
        "is_smaller_reporting_company": False,
        "is_emerging_growth_company": False,
        "fiscal_year_end": "0926",
        "ein": "942404110",
        "phone": "(408) 996-1010",
        "description": None,
        "website": None,
        "investor_website": None,
        "state_of_incorporation": "CA",
        "state_of_incorporation_description": "CA",
        "is_foreign": False,
        "flags": None,
        "business_address": {
            "street1": "ONE APPLE PARK WAY",
            "street2": None,
            "city": "CUPERTINO",
            "state_or_country": "CA",
            "state_or_country_description": "CA",
            "zipcode": "95014",
        },
        "mailing_address": {
            "street1": "ONE APPLE PARK WAY",
            "street2": None,
            "city": "CUPERTINO",
            "state_or_country": "CA",
            "state_or_country_description": "CA",
            "zipcode": "95014",
        },
        "former_names": [
            {"name": "APPLE INC", "from_date": "2007-01-10", "to_date": "2019-08-05"},
            {"name": "APPLE COMPUTER INC", "from_date": "1994-01-26", "to_date": "2007-01-04"},
            {"name": "APPLE COMPUTER INC/ FA", "from_date": "1997-07-28", "to_date": "1997-07-28"},
        ],
        "insider_transaction_for_owner_exists": False,
        "insider_transaction_for_issuer_exists": True,
        "is_company": True,
        "is_individual": False,
        "is_bdc": False,
    }
    golden("company", "aapl", aapl)


@pytest.mark.vcr
def test_company_profile_foreign_incorporated(client: TestClient, golden) -> None:
    # Carnival: US-listed but Bermuda-incorporated; submissions store reflects the
    # CURRENT registration (D0/Bermuda) - older filing headers say R1/Panama
    response = client.get("/company/0000815097")
    assert response.status_code == 200
    ccl = response.json()
    assert ccl["cik"] == "0000815097"
    assert ccl["name"] == "Carnival Corp Ltd."
    assert ccl["tickers"] == ["CCL"]
    assert ccl["exchanges"] == ["NYSE"]
    assert ccl["sic"] == "4400"
    assert ccl["sic_description"] == "Water Transportation"
    assert ccl["fiscal_year_end"] == "1130"
    assert ccl["state_of_incorporation"] == "D0"
    assert ccl["state_of_incorporation_description"] == "Bermuda"
    assert ccl["is_foreign"] is True
    assert ccl["business_address"]["state_or_country"] == "FL"
    assert ccl["former_names"] == [
        {"name": "CARNIVAL CORP", "from_date": "1995-03-21", "to_date": "2026-04-29"},
        {"name": "CARNIVAL CRUISE LINES INC", "from_date": "1994-01-21", "to_date": "1994-01-21"},
    ]
    golden("company", "carnival", ccl)


@pytest.mark.vcr
def test_company_profile_individual(client: TestClient, golden) -> None:
    # individual insider (NVDA EVP Ajay Puri): no ticker/SIC/category, mailing-only
    # address, and display_name reverses the store's "Last First" ordering
    response = client.get("/company/0001347842")
    assert response.status_code == 200
    puri = response.json()
    assert puri["cik"] == "0001347842"
    assert puri["name"] == "Puri Ajay K"
    assert puri["display_name"] == "Ajay K Puri"
    assert puri["entity_type"] == "other"
    assert puri["tickers"] == []
    assert puri["exchanges"] == []
    assert puri["sic"] is None
    assert puri["category"] is None
    assert puri["filer_status"] is None
    # no state code -> foreignness is unknowable from the submissions store alone
    assert puri["is_foreign"] is None
    assert puri["business_address"] is None
    assert puri["mailing_address"] == {
        "street1": "2788 SAN TOMAS EXPRESSWAY",
        "street2": None,
        "city": "SANTA CLARA",
        "state_or_country": "CA",
        "state_or_country_description": "CA",
        "zipcode": "95051",
    }
    assert puri["insider_transaction_for_owner_exists"] is True
    assert puri["insider_transaction_for_issuer_exists"] is False
    assert puri["is_company"] is False
    assert puri["is_individual"] is True
    golden("company", "puri_individual", puri)


@pytest.mark.vcr(allow_playback_repeats=True)
def test_submissions_first_page(client: TestClient, golden) -> None:
    # AAPL full history spans pagination files back to 1994 (2234 filings in cassette)
    response = client.get("/company/AAPL/submissions", params={"page_size": 3})
    assert response.status_code == 200
    page = response.json()
    assert page["cik"] == "0000320193"
    assert page["company"] == "Apple Inc."
    assert page["total"] == 2234
    assert page["start"] == 0
    assert page["page_size"] == 3
    assert page["has_more"] is True
    assert page["next_start"] == 3
    assert len(page["filings"]) == 3
    # newest row: a Form 4 with no act/file_number (ownership filings carry neither)
    assert page["filings"][0] == {
        "accession_number": "0001140361-26-023363",
        "form": "4",
        "filing_date": "2026-05-29",
        "report_date": "2026-05-27",
        "acceptance_datetime": "2026-05-29T22:30:27Z",
        "act": None,
        "file_number": None,
        "items": [],
        "size": 6956,
        "is_xbrl": False,
        "is_inline_xbrl": False,
        "primary_document": "xslF345X06/form4.xml",
        "primary_doc_description": "FORM 4",
    }
    # SD row: act 34 + file number but no report date
    sd = page["filings"][1]
    assert sd["form"] == "SD"
    assert sd["act"] == "34"
    assert sd["file_number"] == "001-36743"
    assert sd["report_date"] is None
    # Form 144 is filed under the 33 Act with no primary doc description
    form144 = page["filings"][2]
    assert form144["form"] == "144"
    assert form144["act"] == "33"
    assert form144["primary_doc_description"] is None
    golden("company_submissions", "aapl_first_page", page)


@pytest.mark.vcr(allow_playback_repeats=True)
def test_submissions_form_filter(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/submissions", params={"form": "10-K", "page_size": 2})
    assert response.status_code == 200
    tenks = response.json()
    assert tenks["total"] == 32
    assert tenks["has_more"] is True
    assert tenks["next_start"] == 2
    assert tenks["filings"][0] == {
        "accession_number": "0000320193-25-000079",
        "form": "10-K",
        "filing_date": "2025-10-31",
        "report_date": "2025-09-27",
        "acceptance_datetime": "2025-10-31T10:01:26Z",
        "act": "34",
        "file_number": "001-36743",
        "items": [],
        "size": 9392337,
        "is_xbrl": True,
        "is_inline_xbrl": True,
        "primary_document": "aapl-20250927.htm",
        "primary_doc_description": "10-K",
    }
    golden("company_submissions", "aapl_10k_filter", tenks)

    # 8-K rows carry item codes split from the store's CSV field
    response = client.get("/company/AAPL/submissions", params={"form": "8-K", "page_size": 1})
    eightks = response.json()
    assert eightks["total"] == 234
    latest = eightks["filings"][0]
    assert latest["accession_number"] == "0000320193-26-000011"
    assert latest["items"] == ["2.02", "9.01"]
    assert latest["is_inline_xbrl"] is True


@pytest.mark.vcr(allow_playback_repeats=True)
def test_submissions_deep_page(client: TestClient, golden) -> None:
    # last page of AAPL history: partial page, paging terminates cleanly
    response = client.get("/company/AAPL/submissions", params={"start": 2230, "page_size": 100})
    assert response.status_code == 200
    deep = response.json()
    assert deep["total"] == 2234
    assert deep["start"] == 2230
    assert len(deep["filings"]) == 4
    assert deep["has_more"] is False
    assert deep["next_start"] is None
    oldest = deep["filings"][-1]
    assert oldest["accession_number"] == "0000320193-94-000002"
    assert oldest["form"] == "10-Q"
    assert oldest["filing_date"] == "1994-01-26"
    golden("company_submissions", "aapl_deep_page", deep)


@pytest.mark.vcr
def test_company_not_found_silence_checks(client: TestClient) -> None:
    # valid-format CIK that exists nowhere at SEC: the submissions fetch 404s
    response = client.get("/company/9999999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "no entity at SEC with CIK 9999999999"

    # unknown ticker resolves locally against the tickers map; detail carries guidance
    response = client.get("/company/ZZZZJUNK")
    assert response.status_code == 404
    assert response.json()["detail"].startswith("Company not found: 'ZZZZJUNK'")


def test_company_param_validation(client: TestClient) -> None:
    # all-digit id beyond the 10-digit CIK ceiling
    response = client.get("/company/99999999990")
    assert response.status_code == 422
    assert "CIK out of range" in response.json()["detail"]
    # whitespace-only id strips to empty
    response = client.get("/company/%20")
    assert response.status_code == 422
    assert response.json()["detail"] == "empty entity id"
    # paging bounds
    assert client.get("/company/AAPL/submissions", params={"start": -1}).status_code == 422
    assert client.get("/company/AAPL/submissions", params={"page_size": 0}).status_code == 422
    assert client.get("/company/AAPL/submissions", params={"page_size": 1001}).status_code == 422
