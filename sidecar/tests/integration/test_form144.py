"""Integration: /filing/{accession} envelope with typed Form 144 `data` (P4).

One `Form144` object backs 144 and 144/A -> one kind (`form144`); `form` is the variant (derived
from is_amendment, since Form144 exposes no `.form`). `data` is the as-filed Rule 144 notice: issuer
identity, the person selling + relationship, and the three XML tables (securities information / how
acquired / sold in past 3 months) + the notice signature's 10b5-1 plan adoption dates. Derived
analytics (totals, percentages, holding-period, 10b5-1 inference, anomaly flags) are excluded -- the
raw rows ship instead. Dates are kept as-filed MM/DD/YYYY strings (the form permits 1933
placeholders). Accessions span:

  abeona    standard single-security 144: 10b5-1 plan adopted, nothing_to_report true
  arbutus   144 with NO plan + a rich 12-row prior-sales table (nothing_to_report false)
  red_robin 144/A amendment, MULTI-security (4 rows), multi-relationship seller (Officer+Director)
  best_buy  144/A amendment: 19 acquisition lots, 10b5-1 plan, one prior sale
  travelzoo 144 by a 10% stockholder ENTITY (not an individual officer)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_ABEONA = "0001972481-25-000063"
_ARBUTUS = "0001959173-25-002349"
_RED_ROBIN = "0001415889-25-008808"
_BEST_BUY = "0001959173-25-002284"
_TRAVELZOO = "0001628280-25-015558"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Form144"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "form144"
    return body


def test_form144_abeona_standard_10b5_1(client: TestClient, golden) -> None:
    data = _data(client, _ABEONA)["data"]
    assert data["form"] == "144"
    assert data["is_amendment"] is False
    assert data["issuer_name"] == "ABEONA THERAPEUTICS INC."
    assert data["issuer_cik"] == "0000318306"  # the ISSUER, distinct from the filer's CIK
    assert data["sec_file_number"] == "001-15771"
    assert data["issuer_contact_phone"] == "646-813-4701"
    assert data["person_selling"] == "Seshadri Vishwas"
    assert data["relationships"] == ["Officer"]
    # filer credentials present but name/file_number absent in this filing's XML -> null (faithful)
    assert data["filer"] == {"cik": "0001865131", "name": None, "file_number": None}
    assert data["contact"] is None
    assert data["issuer_address"]["city"] == "CLEVELAND"
    assert data["issuer_address"]["state_or_country"] == "OH"
    assert data["issuer_address"]["zipcode"] == "44103"
    assert data["nothing_to_report"] is True  # real bool (edgar fix): nothing sold in past 3 months
    assert data["remarks"] is None

    # 10b5-1 plan: the raw adoption date is captured (the is_10b5_1_plan inference is excluded)
    assert data["notice_signature"]["plan_adoption_dates"] == ["09/18/2024"]
    assert data["notice_signature"]["notice_date"] == "03/31/2025"
    assert data["notice_signature"]["signature"].startswith("/s/ James Weimer")

    assert len(data["securities_information"]) == 1
    sec = data["securities_information"][0]
    assert sec == {
        "security_class": "Common Stock",
        "units_to_be_sold": 25000,
        "market_value": 119560.0,
        "units_outstanding": 48533798,
        "approx_sale_date": "03/31/2025",
        "exchange_name": "Nasdaq",
        "broker_name": "Stifel Nicolaus & Company Inc",
        "broker_address": {  # now surfaced (edgar fix): the broker-of-record address
            "street1": "501 N Broadway",
            "street2": None,
            "city": "St. Louis",
            "state_or_country": "MO",
            "state_or_country_description": None,
            "zipcode": "63102",
        },
    }
    # four acquisition lots; none gifts
    assert len(data["securities_to_be_sold"]) == 4
    assert data["securities_to_be_sold"][0]["amount_acquired"] == 8000
    assert all(row["is_gift"] == "N" for row in data["securities_to_be_sold"])
    # nothing sold in past 3 months -> empty table (and nothing_to_report 'Y')
    assert data["securities_sold_past_3_months"] == []

    golden("filing", "form144_abeona", _data(client, _ABEONA))


def test_form144_arbutus_prior_sales_no_plan(client: TestClient, golden) -> None:
    data = _data(client, _ARBUTUS)["data"]
    assert data["form"] == "144"
    assert data["is_amendment"] is False
    assert data["issuer_name"] == "Arbutus Biopharma Corp"
    assert data["issuer_cik"] == "0001447028"
    assert data["person_selling"] == "Sofia Michael J."
    assert data["relationships"] == ["Officer"]
    assert data["nothing_to_report"] is False  # real bool (edgar fix): 12 prior sales reported
    # no 10b5-1 plan: plan_adoption_dates empty (contrast abeona/best_buy)
    assert data["notice_signature"]["plan_adoption_dates"] == []

    sec = data["securities_information"][0]
    assert sec["units_to_be_sold"] == 250000
    assert sec["market_value"] == 875000.0
    assert sec["exchange_name"] == "nasdaq"  # as-filed casing, faithful (abeona filed "Nasdaq")
    assert sec["broker_name"] == "Fidelity Brokerage Services LLC"
    assert sec["broker_address"]["street1"] == "245 Summer Street"  # now surfaced (edgar fix)
    assert sec["broker_address"]["zipcode"] == "02110"

    # rich prior-sales table: 12 disaggregated rows, kept individually
    sales = data["securities_sold_past_3_months"]
    assert len(sales) == 12
    assert sales[0] == {
        "security_class": "Common",
        "seller_name": "Michael Sofia c/o Arbutus Biopharma Corp",
        "sale_date": "03/07/2025",
        "amount_sold": 10000,
        "gross_proceeds": 33600.0,
        "seller_address": {  # now surfaced (edgar fix): the prior seller's address
            "street1": "701 VETERANS CIRCLE",
            "street2": None,
            "city": "WARMINSTER",
            "state_or_country": "PA",
            "state_or_country_description": None,
            "zipcode": "18974",
        },
    }

    golden("filing", "form144_arbutus", _data(client, _ARBUTUS))


def test_form144_red_robin_amendment_multi_security(client: TestClient, golden) -> None:
    data = _data(client, _RED_ROBIN)["data"]
    assert data["form"] == "144/A"
    assert data["is_amendment"] is True
    assert data["issuer_name"] == "RED ROBIN GOURMET BURGERS INC"
    assert data["issuer_cik"] == "0001171759"
    assert data["person_selling"] == "Gerard Johan Hart"
    # multi-relationship seller, order preserved as filed
    assert data["relationships"] == ["Officer", "Director"]
    assert data["nothing_to_report"] is True  # real bool (edgar fix)
    assert data["remarks"].startswith("This Form 144/A amends the Form 144 filed on March 13, 2025")

    # MULTI-security: four distinct securitiesInformation rows (different approx sale dates)
    secs = data["securities_information"]
    assert len(secs) == 4
    assert all(s["security_class"] == "Common Stock" for s in secs)
    assert all(s["broker_name"] == "E*Trade from Morgan Stanley" for s in secs)
    assert [s["approx_sale_date"] for s in secs] == ["03/14/2025", "03/17/2025", "03/21/2025", "03/24/2025"]
    assert len(data["securities_to_be_sold"]) == 2

    golden("filing", "form144_red_robin_amendment", _data(client, _RED_ROBIN))


def test_form144_best_buy_amendment_many_lots(client: TestClient, golden) -> None:
    data = _data(client, _BEST_BUY)["data"]
    assert data["form"] == "144/A"
    assert data["is_amendment"] is True
    assert data["issuer_name"] == "BEST BUY CO INC"
    assert data["issuer_cik"] == "0000764478"
    assert data["person_selling"] == "Bilunas Matthew M"
    assert data["nothing_to_report"] is False  # real bool (edgar fix)
    assert data["remarks"].startswith("This form 144 amends and supersedes")
    assert data["notice_signature"]["plan_adoption_dates"] == ["12/19/2024"]

    sec = data["securities_information"][0]
    assert sec["units_to_be_sold"] == 51000
    assert sec["market_value"] == 3784200.0
    assert sec["exchange_name"] == "NYSE"
    # 19 acquisition lots spanning years (a large securities_to_be_sold table)
    assert len(data["securities_to_be_sold"]) == 19
    # one prior sale, with fractional-cent gross proceeds preserved
    sales = data["securities_sold_past_3_months"]
    assert len(sales) == 1
    assert sales[0]["amount_sold"] == 9482
    assert sales[0]["gross_proceeds"] == 688836.01

    golden("filing", "form144_best_buy_amendment", _data(client, _BEST_BUY))


def test_form144_travelzoo_entity_ten_percent_holder(client: TestClient, golden) -> None:
    data = _data(client, _TRAVELZOO)["data"]
    assert data["form"] == "144"
    assert data["is_amendment"] is False
    assert data["issuer_name"] == "Travelzoo"
    assert data["issuer_cik"] == "0001133311"
    # the seller is an ENTITY (a fund), not an individual officer; relationship is a 10% holder
    assert data["person_selling"] == "Azzurro Capital Inc."
    assert data["relationships"] == ["10% Stockholder"]
    assert data["nothing_to_report"] is False  # real bool (edgar fix)
    assert data["notice_signature"]["signature"] == "/s/ Ralph Bartel, Authorized Signatory"

    sec = data["securities_information"][0]
    assert sec["units_to_be_sold"] == 25000
    assert sec["market_value"] == 340500.0
    assert sec["broker_name"] == "E*Trade Securities LLC"
    sales = data["securities_sold_past_3_months"]
    assert len(sales) == 6
    # foreign seller address surfaces too (edgar fix): Gibraltar, non-US postal code
    assert sales[0]["seller_address"]["city"] == "Gibraltar"
    assert sales[0]["seller_address"]["zipcode"] == "GX11 1AA"

    golden("filing", "form144_travelzoo", _data(client, _TRAVELZOO))
