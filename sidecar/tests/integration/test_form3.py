"""Integration: /filing/{accession} envelope with typed Form 3 `data` (the P4 ownership payload).

Form 3 is the INITIAL statement of beneficial ownership: holdings, never transactions. It reuses the
exact OwnershipData model + converter as Form 4 (obj_type is "Form3"); these cases assert real values
INSIDE `data` and dump `filing/form3_*` goldens for the TS Zod leg. Accessions are 2026 Form 3s chosen
to span the edge-case matrix:

  cytek_no_securities     no_securities flag set (new director, every table empty)
  clearmind_holding       initial non-derivative holding; reporting owner is a COMPANY 10% owner
  bjs_officer             initial non-derivative holding; reporting owner is an officer (officer_title set)
  ameriprise_derivatives  2 non-derivative + 5 derivative holdings; footnoted cells poison whole columns

Column gotcha (extends the U40 footnoted-price finding): edgar's convert_to_numeric coerces a numeric
column to float ONLY when EVERY cell parses; one footnoted cell (e.g. "249.701 [F1]" or a "[F7]" price)
leaves the WHOLE column as raw strings. So Clearmind's shares is 101951.0 (float) while Ameriprise's
shares is "4099" (str) and its option exercise_price is "344.45" (str) -- mirrored faithfully, not coerced.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_CYTEK = "0001181190-26-000004"
_CLEARMIND = "0001475597-26-000079"
_BJS = "0001193125-26-269545"
_AMERIPRISE = "0001184353-26-000005"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Form3"
    assert body["form"] == "3"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "ownership"
    assert data["form"] == "3"
    # Form 3 is an initial holdings statement: never transactions
    assert data["non_derivative_transactions"] == []
    assert data["derivative_transactions"] == []
    return body


def test_form3_cytek_no_securities(client: TestClient, golden) -> None:
    body = _data(client, _CYTEK)
    data = body["data"]
    assert data["issuer"] == {"cik": "0001831915", "name": "Cytek Biosciences, Inc.", "ticker": "CTKB"}

    owner = data["reporting_owners"][0]
    assert owner["name"] == "Glenn P Muir"  # individual -> reversed to display order
    assert owner["name_unreversed"] == "MUIR GLENN P"
    assert owner["is_company"] is False
    assert owner["is_director"] is True
    assert owner["position"] == "Director"
    # the owner address branch (ownership owners carry a full address)
    assert owner["address"]["city"] == "FREMONT"
    assert owner["address"]["state_or_country"] == "CA"

    # no_securities filing: the flag is set and every holdings table is empty
    assert data["no_securities"] is True
    assert data["non_derivative_holdings"] == []
    assert data["derivative_holdings"] == []
    assert data["footnotes"] == {}
    assert data["signatures"][0]["signature"] == "/s/ Valerie Barnett, Attorney-in-Fact"

    golden("filing", "form3_cytek_no_securities", body)


def test_form3_clearmind_company_owner_holding(client: TestClient, golden) -> None:
    body = _data(client, _CLEARMIND)
    data = body["data"]
    assert data["issuer"] == {"cik": "0001892500", "name": "Clearmind Medicine Inc.", "ticker": "CMND"}

    owner = data["reporting_owners"][0]
    # a company 10%-owner: name is NOT reversed, the 10%-owner flag drives the position label
    assert owner["name"] == "HRT FINANCIAL LP"
    assert owner["name_unreversed"] == "HRT FINANCIAL LP"
    assert owner["is_company"] is True
    assert owner["is_ten_pct_owner"] is True
    assert owner["is_director"] is False
    assert owner["position"] == "10% Owner"

    assert data["no_securities"] is False
    holdings = data["non_derivative_holdings"]
    assert len(holdings) == 1
    # column fully numeric -> float (contrast Ameriprise, below)
    assert holdings[0] == {"security": "Common Stock", "shares": 101951.0, "direct": True, "nature_of_ownership": None}
    assert data["derivative_holdings"] == []

    golden("filing", "form3_clearmind_company_owner_holding", body)


def test_form3_bjs_officer_holding(client: TestClient, golden) -> None:
    body = _data(client, _BJS)
    data = body["data"]
    assert data["issuer"] == {"cik": "0001013488", "name": "BJs RESTAURANTS INC", "ticker": "BJRI"}

    owner = data["reporting_owners"][0]
    assert owner["name"] == "Monika Saxena"
    assert owner["is_officer"] is True
    assert owner["is_director"] is False
    assert owner["officer_title"] == "EVP & Brand President"
    assert owner["position"] == "EVP & Brand President"

    holdings = data["non_derivative_holdings"]
    assert len(holdings) == 1
    # a reported holding of zero direct shares is valid (the security class itself is disclosed)
    assert holdings[0]["security"] == "Common Stock"
    assert holdings[0]["shares"] == 0.0
    assert holdings[0]["direct"] is True

    golden("filing", "form3_bjs_officer_holding", body)


def test_form3_ameriprise_derivative_holdings(client: TestClient, golden) -> None:
    body = _data(client, _AMERIPRISE)
    data = body["data"]
    assert data["issuer"] == {"cik": "0000820027", "name": "AMERIPRISE FINANCIAL INC", "ticker": "AMP"}

    owner = data["reporting_owners"][0]
    assert owner["name"] == "Petruzillo Kelli A. Hunter"
    assert owner["name_unreversed"] == "HUNTER PETRUZILLO KELLI A."
    assert owner["is_officer"] is True
    assert owner["officer_title"] == "Exec VP of Human Resources"

    # two non-derivative holdings; the footnoted cell ("249.701 [F1]") poisons the whole shares column
    # to strings, so even the clean "4099" cell stays a string -- never coerced to a number
    ndh = data["non_derivative_holdings"]
    assert len(ndh) == 2
    assert ndh[0] == {"security": "Common Stock", "shares": "4099", "direct": True, "nature_of_ownership": None}
    assert isinstance(ndh[0]["shares"], str), "footnoted column keeps the whole column as raw strings"
    assert ndh[1]["shares"] == "249.701 [F1]"
    assert ndh[1]["direct"] is False
    assert ndh[1]["nature_of_ownership"] == "By 401(k) Plan"

    # five derivative holdings: four dated employee stock options + one phantom-stock position
    dh = data["derivative_holdings"]
    assert len(dh) == 5
    option = dh[0]
    assert option["security"] == "Employee Stock Option (right to buy)"
    assert option["underlying"] == "Common Stock"
    assert option["underlying_shares"] == 921.0  # underlying_shares column is fully numeric -> float
    assert option["exercise_price"] == "344.45"  # poisoned by the phantom-stock "[F7]" price -> string
    assert isinstance(option["exercise_price"], str)
    assert option["exercise_date"] == "[F2]"  # a vesting-schedule footnote stands in for the date
    assert option["expiration_date"] == "2033-01-28"
    assert option["direct_indirect"] == "D"

    phantom = dh[4]
    assert phantom["security"] == "Phantom Stock"
    assert phantom["underlying_shares"] == 1316.417
    assert phantom["exercise_price"] == "[F7]"
    assert phantom["expiration_date"] == "[F6]"

    # the document footnote map resolves every cited id
    assert len(data["footnotes"]) == 7
    assert "401(k)" in data["footnotes"]["F1"]
    assert data["remarks"] == "Exhibit List: Exhibit 24-Power of Attorney"

    golden("filing", "form3_ameriprise_derivative_holdings", body)
