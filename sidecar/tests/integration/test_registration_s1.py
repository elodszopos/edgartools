"""Integration (U53a): the S-1 / F-1 registration family over the one `RegistrationS1` -> kind=registration_s1.

Five fixtures pin the structural matrix. S-1 and F-1 (and /A) all dispatch to RegistrationS1; what
differs is which legs populate:

  accelerant  S-1     real operating-company IPO -> clean cover (state/SIC/EIN), 5-bank underwriting,
                      capitalization table; Exhibit 107 located (exhibit_url set) but its securities/
                      totals do not parse -> fee_table is a non-None shell (distinct from genuine None)
  dboral      S-1     SPAC IPO -> the rich Exhibit 107 leg: total offering + net fee + 4 fee-table
                      securities (units/shares/rights/warrants); offering_type=spac, Rule 415
  juneng      F-1     foreign (Cayman) IPO -> single-security fee table + capitalization w/ equity
  linkage     F-1/A   foreign resale amendment -> the selling-stockholders leg, clean named holders
  cellectar   S-1/A   amendment -> the dilution + capitalization legs (per-share + dollar amounts),
                      single-bank underwriting

edgar's selling-stockholders HTML extractor over-triggers on non-resale IPOs (it lifts header
fragments like "Before Offering" as holder names); dboral/accelerant therefore assert their fee /
underwriting / dilution legs, and only linkage (a genuine resale) asserts selling-stockholder rows.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_ACCELERANT = "0001193125-25-152889"  # S-1 IPO, Accelerant Holdings
_DBORAL = "0001641172-25-017010"  # S-1 SPAC, D. Boral ARC Acquisition II Corp.
_JUNENG = "0001213900-25-058796"  # F-1 IPO, JuNeng Technology Ltd (Cayman)
_LINKAGE = "0001213900-25-059747"  # F-1/A resale, Linkage Global Inc (Cayman)
_CELLECTAR = "0001104659-25-063849"  # S-1/A, Cellectar Biosciences, Inc.


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _s1(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "RegistrationS1"  # S-1 and F-1 (+/A) all -> RegistrationS1
    assert body["data"] is not None
    assert body["data"]["kind"] == "registration_s1"
    return body


def test_s1_ipo_operating_company(client: TestClient, golden) -> None:
    body = _s1(client, _ACCELERANT)
    data = body["data"]
    assert data["form"] == "S-1"
    assert data["is_amendment"] is False
    assert data["offering_type"] == "ipo"
    assert data["company"] == "Accelerant Holdings"

    cover = data["cover_page"]
    assert cover["company_name"] == "Accelerant Holdings"
    assert cover["state_of_incorporation"] == "Cayman Islands"
    assert cover["sic_code"] == "6411"
    assert cover["ein"] == "98-1753044"
    assert cover["confidence"] == "high"
    assert cover["is_rule_415"] is False
    assert cover["is_smaller_reporting_company"] is False
    assert cover["is_emerging_growth_company"] is True

    # Exhibit 107 is located (exhibit_url set) but its securities/totals do not parse -> fee_table
    # is a non-None shell; the genuine fee_table=None branch is covered by linkage/cellectar below
    ft = data["fee_table"]
    assert ft is not None
    assert ft["total_offering_amount"] is None
    assert ft["securities"] == []
    assert ft["exhibit_url"].endswith("d543111dexfilingfees.htm")
    assert data["selling_stockholders"] is None
    assert data["dilution"] is None

    # capitalization extracts (full line-item table) even when the headline scalars do not
    assert data["capitalization"] is not None
    assert len(data["capitalization"]["rows"]) == 16

    uw = data["underwriting"]
    assert uw is not None
    assert [u["name"] for u in uw["underwriters"]] == [
        "Piper Sandler",
        "Wells Fargo Securities",
        "William Blair",
        "Raymond James",
        "TD Securities",
    ]
    golden("filing", "registration_s1_accelerant_ipo", body)


def test_s1_spac_fee_table(client: TestClient, golden) -> None:
    body = _s1(client, _DBORAL)
    data = body["data"]
    assert data["form"] == "S-1"
    assert data["offering_type"] == "spac"
    assert data["company"] == "D. Boral ARC Acquisition II Corp."

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "British Virgin Islands"
    assert cover["sic_code"] == "6770"
    assert cover["is_rule_415"] is True
    assert cover["is_smaller_reporting_company"] is True

    # the rich Exhibit 107 leg
    ft = data["fee_table"]
    assert ft is not None
    assert ft["total_offering_amount"] == 452812500.0
    assert ft["net_fee_due"] == 69325.59
    assert ft["fee_deferred"] is False
    assert len(ft["securities"]) == 4
    sec0 = ft["securities"][0]
    assert sec0["security_type"] == "Equity"
    assert sec0["security_title"].startswith("Units")
    assert sec0["amount_registered"] == "28,750,000"
    assert sec0["price_per_unit"] == 10.0
    assert sec0["max_aggregate_amount"] == 287500000.0
    assert sec0["fee_amount"] == 44016.25

    assert data["dilution"]["public_offering_price"] == "$10.00"
    golden("filing", "registration_s1_dboral_spac", body)


def test_f1_foreign_ipo(client: TestClient, golden) -> None:
    body = _s1(client, _JUNENG)
    data = body["data"]
    assert data["form"] == "F-1"
    assert data["is_amendment"] is False
    assert data["offering_type"] == "ipo"
    assert data["company"] == "JuNeng Technology Ltd"

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "Cayman Islands"
    assert cover["sic_code"] == "7311"
    assert cover["is_emerging_growth_company"] is True

    ft = data["fee_table"]
    assert ft is not None
    assert ft["total_offering_amount"] == 11000000.0
    assert ft["net_fee_due"] == 1684.1
    assert len(ft["securities"]) == 1
    sec0 = ft["securities"][0]
    assert sec0["security_title"].startswith("Ordinary Shares")
    assert sec0["amount_registered"] == "2,200,000"
    assert sec0["price_per_unit"] == 5.0
    assert sec0["max_aggregate_amount"] == 11000000.0
    assert sec0["fee_amount"] == 1684.1

    assert data["capitalization"] is not None
    assert data["capitalization"]["total_stockholders_equity_actual"] == "3,229,374"
    assert data["selling_stockholders"] is None
    golden("filing", "registration_s1_juneng_f1", body)


def test_f1a_resale_selling_stockholders(client: TestClient, golden) -> None:
    body = _s1(client, _LINKAGE)
    data = body["data"]
    assert data["form"] == "F-1/A"
    assert data["is_amendment"] is True
    assert data["offering_type"] == "resale"
    assert data["company"] == "Linkage Global Inc"

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "Cayman Islands"
    assert cover["sic_code"] == "5961"
    assert cover["is_rule_415"] is True

    # the selling-stockholders leg: a genuine resale registration with clean named holders
    ss = data["selling_stockholders"]
    assert ss is not None
    assert len(ss["stockholders"]) == 4
    holder0 = ss["stockholders"][0]
    assert holder0["name"] == "Guo Jian Chen"
    assert holder0["shares_before_offering"] == "1,800,000"
    assert holder0["shares_after_offering"] == "1,800,000"

    assert data["fee_table"] is None
    assert data["dilution"] is None
    golden("filing", "registration_s1_linkage_f1a_resale", body)


def test_s1a_dilution_and_capitalization(client: TestClient, golden) -> None:
    body = _s1(client, _CELLECTAR)
    data = body["data"]
    assert data["form"] == "S-1/A"
    assert data["is_amendment"] is True
    assert data["offering_type"] == "unknown"
    assert data["company"] == "Cellectar Biosciences, Inc."

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "Delaware"
    assert cover["sic_code"] == "2834"
    assert cover["ein"] == "04-3321804"
    assert cover["confidence"] == "high"

    # the dilution leg: per-share offering price + dilution
    dilution = data["dilution"]
    assert dilution is not None
    assert dilution["public_offering_price"] == "$7.94"
    assert dilution["dilution_per_share"] == "$2.10"

    # the capitalization leg: actual-column dollar amounts
    cap = data["capitalization"]
    assert cap is not None
    assert len(cap["rows"]) == 8
    assert cap["cash_actual"] == "13,905,173"
    assert cap["total_stockholders_equity_actual"] == "8,253,389"

    uw = data["underwriting"]
    assert uw is not None
    assert len(uw["underwriters"]) == 1
    assert uw["underwriters"][0]["name"] == "Ladenburg Thalmann & Co. Inc."
    golden("filing", "registration_s1_cellectar_s1a", body)
