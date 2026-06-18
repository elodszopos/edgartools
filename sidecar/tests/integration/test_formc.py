"""Integration: /filing/{accession} envelope with typed Form C `data` (P4).

One `FormC` object backs every Reg Crowdfunding variant -> one kind (`formc`); `form` is the variant.
`data` is the as-filed crowdfunding record: the filer/issuer identity, the funding portal, the offering
terms, the annual-report financials, and signatures. The variant drives which blocks are present:

  griggs       plain C: full structure (offering + annual report + portal), 4 signatures, co_issuer False
  health_care  C/A amendment: co_issuer True, fractional amounts, empty other_desc -> null
  stone_ledge  C-U update: oversub "N", maximum_offering_amount blank -> 0.0, single signature
  earkick      C-AR annual report: offering null, portal null, period set, jurisdictions empty
  bodhi        C-TR termination: offering null AND annual_report null (maximal-null case)

The filer block carries the CCC submission credential (SEC-masked to "XXXXXXXX"), the LIVE/TEST flag,
the copy-routing flags, and the report period (verified: griggs ccc masked + live True + return-copy
True; health_care/earkick override True; earkick C-AR period set).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_GRIGGS = "0001669191-25-000186"
_HEALTH_CARE = "0001670254-25-000134"
_STONE_LEDGE = "0001140361-25-000952"
_EARKICK = "0001670254-25-000227"
_BODHI = "0001665160-25-000483"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "FormC"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "formc"
    return body


def test_formc_griggs_full_structure(client: TestClient, golden) -> None:
    data = _data(client, _GRIGGS)["data"]
    assert data["form"] == "C"

    filer = data["filer"]
    assert filer["cik"] == "0002061971"
    assert filer["ccc"] == "XXXXXXXX"  # CCC submission credential, SEC-masked in public filings
    assert filer["live_or_test"] is True  # a LIVE submission (not a test)
    assert filer["ccc"] != filer["cik"]  # ccc reads <filerCcc>, no longer duplicating the CIK
    assert filer["confirming_copy_flag"] is False
    assert filer["return_copy_flag"] is True
    assert filer["override_internet_flag"] is False
    assert filer["period"] is None  # offering form, no report period

    issuer = data["issuer"]
    assert issuer["name"] == "Griggs Mutual Holdings, LLC"
    assert issuer["legal_status"] == "Limited Liability Company"
    assert issuer["jurisdiction"] == "CA"
    assert issuer["date_of_incorporation"] == "2020-02-18"
    assert issuer["website"] == "https://kribsavup.com/"
    assert issuer["co_issuer"] is False
    assert issuer["address"]["city"] == "Beaumont"
    assert issuer["address"]["state_or_country"] == "CA"
    assert issuer["address"]["zipcode"] == "92223"
    assert issuer["funding_portal"] == {
        "name": "NetCapital Funding Portal Inc.",
        "cik": "0001669191",
        "crd": "283596",
        "file_number": "007-00035",
    }

    offering = data["offering"]
    assert offering["security_offered_type"] == "Common Stock"
    assert offering["security_offered_other_desc"] is None
    assert offering["no_of_security_offered"] == "10000"
    assert offering["price"] == "1.00000"
    assert offering["offering_amount"] == 10000.0
    assert offering["maximum_offering_amount"] == 250000.0
    assert offering["deadline_date"] == "2025-05-30"
    assert offering["over_subscription_accepted"] == "Y"
    assert offering["over_subscription_allocation_type"] == "First-come, first-served basis"
    assert offering["compensation_amount"].startswith("Up to 4.9%")

    report = data["annual_report"]
    assert report["current_employees"] == 0
    assert report["total_asset_most_recent_fiscal_year"] == 12328.0
    assert report["total_asset_prior_fiscal_year"] == 28346.0
    assert report["revenue_most_recent_fiscal_year"] == 0.0
    assert report["revenue_prior_fiscal_year"] == 528.0
    assert report["net_income_most_recent_fiscal_year"] == -106898.0
    assert report["short_term_debt_most_recent_fiscal_year"] == 118350.0
    assert report["long_term_debt_most_recent_fiscal_year"] == 0.0
    assert len(report["offering_jurisdictions"]) == 56

    sig = data["signatures"]
    assert sig["issuer_signature"]["issuer"] == "Griggs Mutual Holdings, LLC"
    assert sig["issuer_signature"]["title"] == "Principal Executive Officer"
    assert [(s["signature"], s["title"]) for s in sig["signatures"]] == [
        ("Timothy Griggs", "Principal Executive Officer"),
        ("Timothy Griggs", "Principal Financial Officer"),
        ("Timothy Griggs", "Principal Accounting Officer"),
        ("Timothy Griggs", "Board Member"),
    ]
    assert all(s["date"] == "2025-03-26" for s in sig["signatures"])

    golden("filing", "formc_griggs", _data(client, _GRIGGS))


def test_formc_health_care_amendment(client: TestClient, golden) -> None:
    data = _data(client, _HEALTH_CARE)["data"]
    assert data["form"] == "C/A"
    assert data["filer"]["cik"] == "0002037345"
    assert data["filer"]["override_internet_flag"] is True

    issuer = data["issuer"]
    assert issuer["name"] == "Health Care Originals, Inc."
    assert issuer["legal_status"] == "Corporation"
    assert issuer["jurisdiction"] == "DE"
    assert issuer["date_of_incorporation"] == "2016-06-27"
    assert issuer["co_issuer"] is True  # a co-issued offering (contrast griggs)
    assert issuer["funding_portal"]["name"] == "Wefunder Portal LLC"
    assert issuer["funding_portal"]["file_number"] == "007-00033"

    offering = data["offering"]
    assert offering["security_offered_type"] == "Preferred Stock"
    assert offering["security_offered_other_desc"] is None  # filed empty -> null (faithful)
    assert offering["financial_interest"] == "No"
    assert offering["no_of_security_offered"] == "32949"
    assert offering["price"] == "1.51750"
    # fractional dollar amounts survive as floats
    assert offering["offering_amount"] == 49998.59
    assert offering["maximum_offering_amount"] == 1234999.16
    assert offering["deadline_date"] == "2025-07-29"
    assert offering["over_subscription_allocation_type"] == "Other"
    assert offering["desc_over_subscription"] == "As determined by the issuer"

    report = data["annual_report"]
    assert report["current_employees"] == 7
    assert report["total_asset_most_recent_fiscal_year"] == 1014947.0
    assert report["net_income_most_recent_fiscal_year"] == -2650362.0
    assert report["long_term_debt_most_recent_fiscal_year"] == 1307945.0

    assert [(s["signature"], s["title"]) for s in data["signatures"]["signatures"]] == [
        ("Sharon Samjitsingh", "CEO & Co-Founder"),
        ("Parinaz Motamedy", "Board Member"),
        ("Keith Wilson", "Managing Partner"),
        ("Jared Dwarika", "COO & Co-Founder"),
    ]

    golden("filing", "formc_health_care_amendment", _data(client, _HEALTH_CARE))


def test_formc_stone_ledge_update(client: TestClient, golden) -> None:
    data = _data(client, _STONE_LEDGE)["data"]
    assert data["form"] == "C-U"
    assert data["filer"]["cik"] == "0001979200"

    issuer = data["issuer"]
    assert issuer["name"] == "Stone Ledge Spirits Co CF, LLC"
    assert issuer["jurisdiction"] == "MO"
    assert issuer["co_issuer"] is True
    assert issuer["funding_portal"]["name"] == "Silicon Prairie Online LLC"
    assert issuer["funding_portal"]["cik"] == "0001711770"
    assert issuer["funding_portal"]["crd"] == "289746"

    offering = data["offering"]
    assert offering["security_offered_type"] == "Other"
    assert offering["security_offered_other_desc"] == "Class B Membership Interest Units"
    assert offering["financial_interest"] == "None"
    assert offering["no_of_security_offered"] == "60"
    assert offering["price"] == "500.00000"
    assert offering["offering_amount"] == 30000.0
    assert offering["maximum_offering_amount"] == 0.0  # filed blank -> edgar coerces to 0.0 (not null)
    assert offering["over_subscription_accepted"] == "N"
    assert offering["over_subscription_allocation_type"] is None
    assert offering["deadline_date"] == "2024-11-08"

    report = data["annual_report"]
    assert report["current_employees"] == 0
    assert report["total_asset_most_recent_fiscal_year"] == 100.0
    assert report["total_asset_prior_fiscal_year"] == 0.0
    assert len(report["offering_jurisdictions"]) == 52

    sigs = data["signatures"]["signatures"]
    assert len(sigs) == 1
    assert sigs[0] == {"signature": "/s/ Mark Sutherland", "title": "Manager", "date": "2024-12-19"}

    golden("filing", "formc_stone_ledge", _data(client, _STONE_LEDGE))


def test_formc_earkick_annual_report(client: TestClient, golden) -> None:
    data = _data(client, _EARKICK)["data"]
    assert data["form"] == "C-AR"
    # the annual report carries a report period (contrast the offering forms' null)
    assert data["filer"]["period"] == "2024-12-31"
    assert data["filer"]["live_or_test"] is True  # LIVE flag now parses on the C-AR variant too
    assert data["filer"]["override_internet_flag"] is True

    issuer = data["issuer"]
    assert issuer["name"] == "Earkick Inc."
    assert issuer["jurisdiction"] == "DE"
    assert issuer["date_of_incorporation"] == "2021-04-05"
    assert issuer["website"] == "https://earkick.com/"
    assert issuer["funding_portal"] is None  # C-AR has no portal

    assert data["offering"] is None  # C-AR has no offering block

    report = data["annual_report"]
    assert report["current_employees"] == 8
    assert report["total_asset_most_recent_fiscal_year"] == 2137320.0
    assert report["total_asset_prior_fiscal_year"] == 1819043.0
    assert report["revenue_most_recent_fiscal_year"] == 38108.0
    assert report["revenue_prior_fiscal_year"] == 1945.0
    assert report["net_income_most_recent_fiscal_year"] == -213888.0
    assert report["cash_equi_most_recent_fiscal_year"] == 144557.0
    assert report["long_term_debt_most_recent_fiscal_year"] == 1514925.0
    assert report["offering_jurisdictions"] == []  # none listed -> empty

    assert [(s["signature"], s["title"]) for s in data["signatures"]["signatures"]] == [
        ("Herbert Bay", "CEO & Co-Founder"),
        ("Karin Andrea Stephan", "COO & Co-Founder"),
    ]

    golden("filing", "formc_earkick", _data(client, _EARKICK))


def test_formc_bodhi_termination(client: TestClient, golden) -> None:
    data = _data(client, _BODHI)["data"]
    assert data["form"] == "C-TR"
    assert data["filer"]["cik"] == "0001952258"
    assert data["filer"]["period"] is None

    issuer = data["issuer"]
    assert issuer["name"] == "Bodhi NeuroTech, Inc"
    assert issuer["jurisdiction"] == "SC"
    assert issuer["date_of_incorporation"] == "2017-05-31"
    assert issuer["website"] == "https://zendomeditation.com/"
    assert issuer["co_issuer"] is False
    assert issuer["funding_portal"] is None

    # termination report: neither offering nor annual report present (maximal-null case)
    assert data["offering"] is None
    assert data["annual_report"] is None

    sig = data["signatures"]
    assert sig["issuer_signature"]["issuer"] == "Bodhi NeuroTech, Inc"
    assert [(s["signature"], s["title"]) for s in sig["signatures"]] == [
        ("Bashar Badran", "CEO, Principal Executive Officer and Director"),
        ("Edward Baron Short", "Chief Health Officer, Secretary, Treasurer, principal accounting officer, and Director"),
        ("Christian Stiller", "Director"),
    ]
    assert all(s["date"] == "2025-03-25" for s in sig["signatures"])

    golden("filing", "formc_bodhi", _data(client, _BODHI))
