"""Integration: /filing/{accession} envelope with typed Form 5 `data` (the P4 ownership payload).

Form 5 is the ANNUAL statement of changes -- the deferred/exempt transactions (and standing holdings)
not reported during the year. It reuses the exact OwnershipData model + converter as Forms 3/4
(obj_type is "Form5"); these cases assert real values INSIDE `data` and dump `filing/form5_*` goldens.
Accessions are 2026 Form 5s chosen to span the annual-summary edge cases:

  ross_gifts             multiple indirect holdings (Partnership/Trust) + Gift (G) transactions
  oxford_footnoted_txns  reporting owner is BOTH director and officer; J/A transactions cite footnotes
  tjx_dividend_reinvest  canonical annual summary: a run of L-code (dividend-reinvestment) acquisitions
  fortinet_inline_fn     holdings whose nature_of_ownership carries an inline footnote ref ("By Trust [F2]")

The shared 3/5 "derivative holdings" matrix cell is covered by U41 (Form 3 Ameriprise); Form 5's own
contribution here is the annual NON-derivative transaction summary across codes L/G/J/A/P.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_ROSS = "0001238943-26-000002"
_OXFORD = "0000075288-26-000004"
_TJX = "0001411764-26-000002"
_FORTINET = "0001302110-26-000026"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _data(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Form5"
    assert body["form"] == "5"
    data = body["data"]
    assert data is not None
    assert data["kind"] == "ownership"
    assert data["form"] == "5"
    return body


def _by_code(rows: list[dict], code: str) -> list[dict]:
    return [r for r in rows if r["transaction_code"] == code]


def test_form5_ross_gifts_and_indirect_holdings(client: TestClient, golden) -> None:
    body = _data(client, _ROSS)
    data = body["data"]
    assert data["issuer"] == {"cik": "0000745732", "name": "ROSS STORES, INC.", "ticker": "ROST"}

    owner = data["reporting_owners"][0]
    assert owner["name"] == "George Orban"
    assert owner["is_director"] is True
    assert owner["position"] == "Director"

    # standing holdings: one direct + several indirect, the indirect nature labels preserved verbatim
    holdings = data["non_derivative_holdings"]
    assert len(holdings) == 5
    assert holdings[0] == {"security": "Common Stock", "shares": 408176.0, "direct": True, "nature_of_ownership": None}
    indirect_natures = {h["nature_of_ownership"] for h in holdings if h["direct"] is False}
    assert indirect_natures == {"Partnership", "Trust III", "Trust V", "Trust VI"}

    # the annual summary: three gifts (code G -> "Gift"), zero price, indirect
    # per-row form is the originally-reportable form (gifts are Form 4 events deferred to annual)
    gifts = _by_code(data["non_derivative_transactions"], "G")
    assert len(gifts) == 3
    for gift in gifts:
        assert gift["form"] == "4"
        assert gift["transaction_type"] == "Gift"
        assert gift["price"] == 0.0
        assert gift["acquired_disposed"] == "A"
        assert gift["direct_indirect"] == "I"

    golden("filing", "form5_ross_gifts_and_indirect_holdings", body)


def test_form5_oxford_director_officer_footnoted_transactions(client: TestClient, golden) -> None:
    body = _data(client, _OXFORD)
    data = body["data"]
    assert data["issuer"] == {"cik": "0000075288", "name": "OXFORD INDUSTRIES INC", "ticker": "OXM"}

    # the reporting owner is BOTH a director and an officer (both flags set)
    owner = data["reporting_owners"][0]
    assert owner["name"] == "Thomas Caldecot Chubb III"
    assert owner["is_director"] is True
    assert owner["is_officer"] is True
    assert owner["officer_title"] == "CEO and President"

    # GRAT/trust holdings, all indirect
    holdings = data["non_derivative_holdings"]
    assert len(holdings) == 4
    assert all(h["direct"] is False for h in holdings)
    assert "By 2025-3 GRAT" in {h["nature_of_ownership"] for h in holdings}

    # every transaction cites a footnote (the GRAT annuity transfers); J = "Other", A = "Award"
    txns = data["non_derivative_transactions"]
    assert len(txns) == 4
    assert all(t["footnote_ids"] for t in txns), "each Form 5 transaction here cites a footnote"
    assert {t["transaction_code"] for t in txns} == {"J", "A"}
    award = _by_code(txns, "A")[0]
    assert award["transaction_type"] == "Award"
    assert award["footnote_ids"] == ["F2"]
    assert "F2" in data["footnotes"]

    golden("filing", "form5_oxford_director_officer_footnoted_transactions", body)


def test_form5_tjx_annual_dividend_reinvestment(client: TestClient, golden) -> None:
    body = _data(client, _TJX)
    data = body["data"]
    assert data["issuer"] == {"cik": "0000109198", "name": "TJX COMPANIES INC /DE/", "ticker": "TJX"}
    assert data["reporting_owners"][0]["name"] == "Jose B Alvarez"

    # canonical annual summary: a run of small L-code (dividend-reinvestment) acquisitions, no holdings table
    assert data["non_derivative_holdings"] == []
    reinvestments = _by_code(data["non_derivative_transactions"], "L")
    assert len(reinvestments) == 5
    first = reinvestments[0]
    assert first["security"] == "Common Stock"
    assert first["date"] == "2024-12-05"
    assert first["shares"] == 5.1
    assert first["price"] == 124.99
    assert first["acquired_disposed"] == "A"
    # the late-reporting reason is disclosed in the footnote map
    assert "dividend reinvestment" in data["footnotes"]["F1"]

    golden("filing", "form5_tjx_annual_dividend_reinvestment", body)


def test_form5_fortinet_inline_footnote_holdings(client: TestClient, golden) -> None:
    body = _data(client, _FORTINET)
    data = body["data"]
    assert data["issuer"] == {"cik": "0001262039", "name": "Fortinet, Inc.", "ticker": "FTNT"}
    assert data["reporting_owners"][0]["name"] == "Ming Hsieh"

    holdings = data["non_derivative_holdings"]
    assert len(holdings) == 3
    assert holdings[0] == {"security": "Common Stock", "shares": 53914.0, "direct": True, "nature_of_ownership": None}
    # a footnote reference can appear INLINE inside a string cell -- kept verbatim, resolved via the map
    assert holdings[1]["nature_of_ownership"] == "By Trust [F2]"
    assert holdings[1]["direct"] is False
    assert "F2" in data["footnotes"]

    # a single late-reported purchase (P), plus a populated remarks field
    purchases = _by_code(data["non_derivative_transactions"], "P")
    assert len(purchases) == 1
    assert purchases[0]["transaction_type"] == "Purchase"
    assert purchases[0]["price"] == 53.57
    assert data["remarks"].startswith("The holdings set forth in Column 5 of Table I")

    golden("filing", "form5_fortinet_inline_footnote_holdings", body)
