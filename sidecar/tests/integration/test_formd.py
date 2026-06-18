"""Integration: /filing/{accession} envelope with typed Form D `data` (P4).

One `FormD` object backs D and D/A -> one kind (`formd`); `submission_type` is the variant. `data` is
the as-filed Reg D exempt-offering notice: the primary issuer, related persons, the offering block
(industry / exemptions / security type / amounts / investors / sales compensation / use of proceeds),
and signatures. Dollar amounts and counts are as-filed strings ("Indefinite" survives). `is_amendment`
is read from edgar's inverted-name `offering_data.is_new` (verified D=False vs D/A=True below).

A sales-compensation recipient carries the associated broker-dealer name (null when filed empty), the
address with zipcode, and the foreignSolicitation flag (verified on Carlyle/Galaxy below). A related
person carries its ROLE list (Executive Officer / Director / Promoter -- a person can hold several), an
optional middle name, and a free-text relationship clarification (all previously dropped). Co-issuers
from issuerList ride `additional_issuers` ([] for these single-issuer fixtures). Accessions span:

  centerseat  plain operating-company D (tech startup): equity, finite partial raise, no recipients
  one_way     VC fund D: pooled, investment_fund_info, $0 sold, related-person ENTITIES (first_name "-")
  carlyle     D/A amendment: Indefinite offering, 3 sales-compensation recipients (foreign BDs)
  socotra     D/A amendment: non-pooled REIT, FINITE large offering (contrast Indefinite funds)
  ats         D (new): fully sold (amount == sold, remaining 0), 6 related persons
  galaxy      D/A amendment: hedge fund, single 06c exemption, 2 recipients
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_CENTERSEAT = "0002054457-25-000001"
_ONE_WAY = "0002052458-25-000001"
_CARLYLE = "0001938485-25-000002"
_SOCOTRA = "0001573807-25-000001"
_ATS = "0002057270-25-000001"
_GALAXY = "0001794448-25-000001"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "FormD"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "formd"
    return body


def test_formd_centerseat_operating_company(client: TestClient, golden) -> None:
    data = _data(client, _CENTERSEAT)["data"]
    assert data["submission_type"] == "D"
    assert data["is_live"] is True

    issuer = data["primary_issuer"]
    assert issuer["cik"] == "0002054457"
    assert issuer["entity_name"] == "CenterSeat, Inc."
    assert issuer["entity_type"] == "Corporation"
    assert issuer["jurisdiction"] == "DELAWARE"
    assert issuer["phone_number"] == "512-656-1505"
    assert issuer["year_of_incorporation"] == "2024"
    assert issuer["incorporated_within_5_years"] is True
    assert issuer["primary_address"]["city"] == "AUSTIN"
    assert issuer["primary_address"]["state_or_country"] == "TX"
    assert issuer["primary_address"]["zipcode"] == "78756"
    assert data["additional_issuers"] == []  # single-issuer offering -- co-issuer list empty

    assert [(p["first_name"], p["last_name"]) for p in data["related_persons"]] == [
        ("Thomas", "Kopecky"),
        ("Matthew", "Thompson"),
        ("Morgan", "Flager"),
    ]
    # related-person ROLES + clarifications were previously dropped; now carried per person
    assert [p["relationships"] for p in data["related_persons"]] == [
        ["Executive Officer", "Director"],
        ["Director"],
        ["Director"],
    ]
    assert all(p["middle_name"] is None for p in data["related_persons"])
    assert all(p["relationship_clarification"] is None for p in data["related_persons"])

    offering = data["offering"]
    assert offering["is_amendment"] is False  # a new D, not an amendment (edgar's is_new == False here)
    assert offering["is_equity"] is True
    assert offering["is_pooled_investment"] is False
    assert offering["industry_group"]["industry_group_type"] == "Other Technology"
    assert offering["industry_group"]["investment_fund_info"] is None  # operating company, not a fund
    assert offering["federal_exemptions"] == ["06b"]
    assert offering["date_of_first_sale"] == "2025-01-16"
    assert offering["more_than_one_year"] is False
    assert offering["minimum_investment"] == "0"
    assert offering["offering_sales_amounts"] == {
        "total_offering_amount": "2750000",
        "total_amount_sold": "2395000",
        "total_remaining": "355000",
        "clarification_of_response": None,  # empty clarification -> null
    }
    assert offering["investors"] == {"has_non_accredited_investors": False, "total_already_invested": "8"}
    assert offering["sales_compensation_recipients"] == []

    sig = data["signatures"]
    assert sig["authorized_representative"] is False
    assert len(sig["signatures"]) == 1
    assert sig["signatures"][0]["name_of_signer"] == "Thomas Kopecky"
    assert sig["signatures"][0]["title"] == "Chief Executive Officer"
    assert sig["signatures"][0]["date"] == "2025-01-30"

    golden("filing", "formd_centerseat", _data(client, _CENTERSEAT))


def test_formd_one_way_venture_fund(client: TestClient, golden) -> None:
    data = _data(client, _ONE_WAY)["data"]
    assert data["submission_type"] == "D"
    offering = data["offering"]
    assert offering["is_amendment"] is False
    assert offering["is_pooled_investment"] is True
    assert offering["is_equity"] is False
    # fund issuer -> investment_fund_info present (contrast the operating company's null)
    assert offering["industry_group"]["industry_group_type"] == "Pooled Investment Fund"
    assert offering["industry_group"]["investment_fund_info"] == {
        "investment_fund_type": "Venture Capital Fund",
        "is_40_act": False,
    }
    assert offering["federal_exemptions"] == ["06b", "3C", "3C.7"]
    assert offering["date_of_first_sale"] is None  # filed blank -> null (no first sale yet)
    # finite target, nothing sold yet
    assert offering["offering_sales_amounts"]["total_offering_amount"] == "60000000"
    assert offering["offering_sales_amounts"]["total_amount_sold"] == "0"
    assert offering["investors"]["total_already_invested"] == "0"
    assert offering["use_of_proceeds"]["clarification_of_response"].startswith("The Issuer's General Partner")

    # related persons include the GP and management ENTITIES, filed with first_name "-" (faithful)
    persons = data["related_persons"]
    assert len(persons) == 5
    # the GP entity row -- now carrying its role + the free-text clarification (the reason it is listed)
    assert persons[0] == {
        "first_name": "-",
        "middle_name": None,
        "last_name": "One Way Ventures GP III, L.L.C.",
        "address": persons[0]["address"],
        "relationships": ["Executive Officer"],
        "relationship_clarification": "General Partner of the Issuer",
    }
    assert ("Semyon", "Dukach") in [(p["first_name"], p["last_name"]) for p in persons]
    assert data["additional_issuers"] == []

    golden("filing", "formd_one_way", _data(client, _ONE_WAY))


def test_formd_carlyle_amendment_with_recipients(client: TestClient, golden) -> None:
    data = _data(client, _CARLYLE)["data"]
    assert data["submission_type"] == "D/A"
    issuer = data["primary_issuer"]
    assert issuer["entity_name"] == "Carlyle Asia Partners VI - EU, S.C.Sp."
    assert issuer["cik"] == "0001938485"
    assert issuer["jurisdiction"] == "LUXEMBOURG"
    assert data["additional_issuers"] == []

    # the two lead persons are PROMOTERS (the only Promoter-role example) with clarifications
    persons = data["related_persons"]
    assert [p["relationships"] for p in persons[:2]] == [["Promoter"], ["Promoter"]]
    assert persons[0]["relationship_clarification"] == "Cayman General Partner of the Issuer"

    offering = data["offering"]
    assert offering["is_amendment"] is True  # D/A -> edgar's is_new == True (inverted name; verified)
    assert offering["offering_sales_amounts"]["total_offering_amount"] == "Indefinite"
    assert offering["offering_sales_amounts"]["total_amount_sold"] == "292000000"
    assert offering["sales_commission_finders_fees"]["sales_commission"] == "541763"
    assert offering["sales_commission_finders_fees"]["clarification_of_response"].startswith("Employees of affiliate")

    recipients = offering["sales_compensation_recipients"]
    assert len(recipients) == 3
    tcg = recipients[0]
    assert tcg["name"] == "TCG Capital Markets L.L.C."
    assert tcg["crd"] == "291767"
    assert tcg["states_of_solicitation"] == ["All States"]
    assert tcg["address"]["city"] == "New York"
    assert tcg["address"]["state_or_country"] == "NY"
    # edgar fix: associated_bd_name resolves (TCG names its own BD; the other two filed it empty -> null),
    # recipient zipcodes parse (US zip + two foreign postal codes), and foreignSolicitation is captured
    assert [r["associated_bd_name"] for r in recipients] == ["TCG Capital Markets L.L.C.", None, None]
    assert [r["address"]["zipcode"] for r in recipients] == ["10017", "757KY19006", "5885849"]
    assert [r["foreign_solicitation"] for r in recipients] == [False, True, True]
    # foreign broker-dealers carry the country code + description, no US state
    assert recipients[1]["address"]["state_or_country_description"] == "CAYMAN ISLANDS"
    assert recipients[2]["crd"] is None  # filed blank -> null

    golden("filing", "formd_carlyle_amendment", _data(client, _CARLYLE))


def test_formd_socotra_amendment_finite_offering(client: TestClient, golden) -> None:
    data = _data(client, _SOCOTRA)["data"]
    assert data["submission_type"] == "D/A"
    assert data["primary_issuer"]["entity_name"] == "SOCOTRA FUND, LLC"
    assert data["primary_issuer"]["cik"] == "0001573807"
    # empty yearOfInc/value -> null (faithful)
    assert data["primary_issuer"]["year_of_incorporation"] is None

    offering = data["offering"]
    assert offering["is_amendment"] is True
    assert offering["is_pooled_investment"] is False  # a REIT, not a pooled fund
    assert offering["industry_group"]["industry_group_type"] == "REITS and Finance"
    assert offering["industry_group"]["investment_fund_info"] is None
    assert offering["minimum_investment"] == "25000"
    assert offering["date_of_first_sale"] == "2013-04-02"
    # FINITE large offering (contrast the Indefinite funds): remaining is offer - sold
    assert offering["offering_sales_amounts"]["total_offering_amount"] == "750000000"
    assert offering["offering_sales_amounts"]["total_amount_sold"] == "257524872"
    assert offering["offering_sales_amounts"]["total_remaining"] == "492475128"
    assert offering["investors"]["total_already_invested"] == "1219"
    assert offering["sales_compensation_recipients"] == []
    assert len(data["related_persons"]) == 5
    persons = data["related_persons"]
    # tri-role person (all three relationships at once) + a middle name elsewhere in the list
    assert persons[0]["relationships"] == ["Executive Officer", "Director", "Promoter"]
    assert persons[0]["relationship_clarification"] == "President and CEO of Socotra Management, Inc."
    assert persons[4]["middle_name"] == "K."  # David K. Herzer
    assert persons[4]["relationship_clarification"] is None
    assert data["additional_issuers"] == []

    golden("filing", "formd_socotra_amendment", _data(client, _SOCOTRA))


def test_formd_ats_fully_sold(client: TestClient, golden) -> None:
    data = _data(client, _ATS)["data"]
    assert data["submission_type"] == "D"
    offering = data["offering"]
    assert offering["is_amendment"] is False
    assert offering["industry_group"]["industry_group_type"] == "Investing"
    # fully subscribed: amount sold == amount offered, remaining 0
    assert offering["offering_sales_amounts"]["total_offering_amount"] == "294522479"
    assert offering["offering_sales_amounts"]["total_amount_sold"] == "294522479"
    assert offering["offering_sales_amounts"]["total_remaining"] == "0"
    assert offering["investors"]["total_already_invested"] == "4"
    assert offering["minimum_investment"] == "0"
    assert len(data["related_persons"]) == 6
    assert data["primary_issuer"]["entity_name"] == "ATS Holdings, LLC"

    persons = data["related_persons"]
    # middleName is filed for several persons (previously dropped); "Manager" clarifications vary
    assert [p["middle_name"] for p in persons] == ["W.", "W.", None, None, None, "J."]
    assert persons[0]["relationships"] == ["Executive Officer", "Director"]
    assert persons[0]["relationship_clarification"] == "Manager"
    assert persons[2]["relationship_clarification"] is None  # Kenneth Reger filed none
    assert data["additional_issuers"] == []

    golden("filing", "formd_ats", _data(client, _ATS))


def test_formd_galaxy_amendment_hedge_fund(client: TestClient, golden) -> None:
    data = _data(client, _GALAXY)["data"]
    assert data["submission_type"] == "D/A"
    assert data["primary_issuer"]["entity_name"] == "Galaxy Bitcoin Fund LP"

    offering = data["offering"]
    assert offering["is_amendment"] is True
    assert offering["industry_group"]["investment_fund_info"] == {
        "investment_fund_type": "Hedge Fund",
        "is_40_act": False,
    }
    assert offering["revenue_range"] is None  # not filed -> null
    assert offering["federal_exemptions"] == ["06c"]  # single exemption (contrast the multi-rule funds)
    assert offering["offering_sales_amounts"]["total_offering_amount"] == "Indefinite"
    assert offering["offering_sales_amounts"]["total_amount_sold"] == "89672272"

    recipients = offering["sales_compensation_recipients"]
    assert [r["name"] for r in recipients] == ["CAIS Capital LLC", "Morgan Stanley Smith Barney LLC"]
    assert recipients[0]["crd"] == "154512"
    # both BDs filed associated_bd empty -> null; zipcodes now parse; both domestic (foreign False)
    assert all(r["associated_bd_name"] is None for r in recipients)
    assert [r["address"]["zipcode"] for r in recipients] == ["10022", "10577"]
    assert all(r["foreign_solicitation"] is False for r in recipients)

    # every related person is an Executive Officer with the same clarification
    assert all(p["relationships"] == ["Executive Officer"] for p in data["related_persons"])
    assert data["additional_issuers"] == []

    golden("filing", "formd_galaxy_amendment", _data(client, _GALAXY))
