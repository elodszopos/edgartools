"""Integration: /tickers (SEC company ticker map)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.vcr
def test_tickers_full_map_and_paging(client: TestClient, golden) -> None:
    # default request serves the entire map in one page
    response = client.get("/tickers")
    assert response.status_code == 200
    full = response.json()
    assert full["total"] > 5000
    assert len(full["tickers"]) == full["total"]
    assert full["has_more"] is False
    assert full["next_start"] is None

    by_ticker = {ref["ticker"]: ref for ref in full["tickers"]}
    apple = by_ticker["AAPL"]
    assert apple == {"cik": "0000320193", "ticker": "AAPL", "name": "Apple Inc.", "exchange": "Nasdaq"}
    assert by_ticker["JPM"]["exchange"] == "NYSE"
    # every row has a padded CIK and a non-empty ticker
    assert all(len(ref["cik"]) == 10 for ref in full["tickers"])
    assert all(ref["ticker"] for ref in full["tickers"])

    # paging: small page for the golden, second page disjoint
    response = client.get("/tickers", params={"page_size": 5})
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1["tickers"]) == 5
    assert page1["has_more"] is True
    assert page1["next_start"] == 5

    response = client.get("/tickers", params={"page_size": 5, "start": 5})
    page2 = response.json()
    assert {r["ticker"] for r in page1["tickers"]}.isdisjoint({r["ticker"] for r in page2["tickers"]})

    golden("tickers", "first_page", page1)
