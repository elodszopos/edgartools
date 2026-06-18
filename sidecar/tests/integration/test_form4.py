"""Integration: /filing/{accession} envelope with typed Form 4 `data` (the P4 ownership payload).

Every case asserts real values INSIDE `data` (issuer, owner, transaction amounts/dates), never bare
parse-success, and dumps the full envelope as a `filing/form4_*` golden for the TS Zod leg. Accessions
are 2026-Q2 Form 4s mined from the KD fixture set, chosen to span the edge-case matrix:

  ionis_exercise  option exercise (M) + sale (S) + derivative/underlying + expiration + aff10b5One true
  amg_buy         open-market purchase (P), direct, aff10b5One false
  axp_footnoted   derivative award with a FOOTNOTED (null) exercise price
  bofa_amendment  Form 4/A amendment, two reporting owners (both companies -> names not reversed)
  aflac_award     non-derivative award (A) at a zero price
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_IONIS = "0000874015-26-000183"
_AMG = "0001004434-26-000053"
_AXP = "0000004962-26-000232"
_BOFA = "0000070858-26-000255"
_AFLAC = "0000004977-26-000074"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Form4"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "ownership"
    return body


def _by_code(rows: list[dict], code: str) -> list[dict]:
    return [r for r in rows if r["transaction_code"] == code]


def test_form4_ionis_exercise(client: TestClient, golden) -> None:
    body = _data(client, _IONIS)
    data = body["data"]
    assert body["form"] == "4"
    assert data["form"] == "4"

    assert data["issuer"] == {"cik": "0000874015", "name": "IONIS PHARMACEUTICALS INC", "ticker": "IONS"}
    assert data["aff_10b5_one"] is True  # document-level Rule 10b5-1 affirmation (edgar fix surfaces it)

    owner = data["reporting_owners"][0]
    assert owner["name_unreversed"] == "LOSCALZO JOSEPH"
    assert owner["name"] == "Joseph Loscalzo"  # individual -> reversed to display order
    assert owner["is_company"] is False

    # option exercises (M) acquire common stock at the option strike; a sale (S) also present
    exercises = _by_code(data["non_derivative_transactions"], "M")
    assert exercises, "expected option-exercise (M) common-stock rows"
    assert any(r["security"] == "Common Stock" and r["shares"] == 10968.0 and r["price"] == 38.06 for r in exercises)
    assert _by_code(data["non_derivative_transactions"], "S"), "expected a sale (S) row"

    # the derivative leg: a stock option on common stock, dated expiration
    deriv = data["derivative_transactions"]
    assert deriv, "expected derivative transactions"
    option = deriv[0]
    assert option["underlying"] == "Common Stock"
    assert option["exercise_price"] == 38.06
    assert option["expiration_date"] == "2032-06-30"

    golden("filing", "form4_ionis_exercise", body)


def test_form4_amg_buy(client: TestClient, golden) -> None:
    body = _data(client, _AMG)
    data = body["data"]
    assert data["issuer"]["name"] == "AFFILIATED MANAGERS GROUP, INC."
    assert data["issuer"]["ticker"] == "AMG"
    assert data["aff_10b5_one"] is False  # no 10b5-1 affirmation on this open-market buy (contrast ionis)
    assert data["reporting_owners"][0]["name_unreversed"] == "Cates G. Staley"

    buys = _by_code(data["non_derivative_transactions"], "P")
    assert len(buys) == 1
    buy = buys[0]
    assert buy["security"] == "Common Stock"
    assert buy["shares"] == 1500.0
    assert buy["price"] == 305.83
    assert buy["acquired_disposed"] == "A"
    assert buy["direct_indirect"] == "D"

    golden("filing", "form4_amg_buy", body)


def test_form4_axp_footnoted_price(client: TestClient, golden) -> None:
    body = _data(client, _AXP)
    data = body["data"]
    assert data["issuer"]["name"] == "AMERICAN EXPRESS CO"
    assert data["reporting_owners"][0]["name_unreversed"] == "PHILLIPS JR CHARLES E"
    assert data["reporting_owners"][0]["is_director"] is True

    # the award's exercise price is given only by a footnote -> kept as the raw footnote-reference
    # string ("[F1]"), never invented as a number; the cited footnote resolves in the map
    award = data["derivative_transactions"][0]
    assert award["security"] == "Share Equivalent Units"
    assert award["underlying"] == "Common Stock"
    assert award["exercise_price"] == "[F1]"
    assert award["transaction_code"] == "A"
    assert award["footnote_ids"], "expected the footnote id cited by the transaction coding"
    assert "F1" in data["footnotes"], "the footnoted price's footnote must resolve to text"

    golden("filing", "form4_axp_footnoted", body)


def test_form4_bofa_amendment_multiowner(client: TestClient, golden) -> None:
    body = _data(client, _BOFA)
    data = body["data"]
    assert body["form"] == "4/A"  # amendment
    assert data["form"] == "4/A"  # documentType carries the /A suffix on amendments

    owners = data["reporting_owners"]
    assert len(owners) == 2
    # both reporting owners are companies -> the display name is NOT reversed
    for owner in owners:
        assert owner["is_company"] is True
        assert owner["name"] == owner["name_unreversed"]
    assert {o["name_unreversed"] for o in owners} == {
        "BANK OF AMERICA CORP /DE/",
        "Banc of America Preferred Funding Corp",
    }

    golden("filing", "form4_bofa_amendment", body)


def test_form4_aflac_award(client: TestClient, golden) -> None:
    body = _data(client, _AFLAC)
    data = body["data"]
    assert data["issuer"]["name"] == "AFLAC INC"
    assert data["issuer"]["ticker"] == "AFL"
    assert data["reporting_owners"][0]["name_unreversed"] == "Lloyd Karole"

    awards = _by_code(data["non_derivative_transactions"], "A")
    assert awards, "expected an award (A) row"
    assert awards[0]["acquired_disposed"] == "A"

    golden("filing", "form4_aflac_award", body)
