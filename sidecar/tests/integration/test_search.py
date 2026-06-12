"""Integration: /search (EFTS full-text). Every call is a small JSON page served from the store."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_search_paging_filters_and_facets(client: TestClient, golden) -> None:
    # phrase search scoped to 8-K within a fixed window (deterministic fixtures)
    params = {
        "q": '"cybersecurity incident"',
        "forms": "8-K",
        "date_from": "2024-01-01",
        "date_to": "2024-06-30",
        "page_size": 10,
    }
    response = client.get("/search", params=params)
    assert response.status_code == 200
    page1 = response.json()
    assert page1["query"] == '"cybersecurity incident"'
    assert page1["total"] > 100
    assert page1["total_relation"] in ("eq", "gte")
    assert len(page1["results"]) == 10
    assert page1["has_more"] is True
    assert page1["next_start"] == 10
    for result in page1["results"]:
        assert result["form"] in ("8-K", "8-K/A")
        assert "2024-01-01" <= result["filed"] <= "2024-06-30"
        assert result["cik"] is None or len(result["cik"]) == 10
        assert result["score"] > 0
    # facets come back populated for a broad query
    assert len(page1["aggregations"]["forms"]) > 0
    assert len(page1["aggregations"]["entities"]) > 0

    # ground truth pinned from the recorded window (verified against EDGAR full-text search)
    assert page1["total"] == 200
    assert page1["total_relation"] == "eq"
    first = page1["results"][0]
    assert first["accession_number"] == "0001193125-24-147625"
    assert first["form"] == "8-K/A"
    assert first["cik"] == "0000790816"
    assert first["filed"] == "2024-05-28"
    assert first["items"] == ["1.05"]
    assert first["document_id"] == "d774339d8ka.htm"

    # page 2 is disjoint
    response = client.get("/search", params={**params, "start": 10})
    assert response.status_code == 200
    page2 = response.json()
    ids1 = {(r["accession_number"], r["document_id"]) for r in page1["results"]}
    ids2 = {(r["accession_number"], r["document_id"]) for r in page2["results"]}
    assert ids1.isdisjoint(ids2)

    # structured lookup: 8-K Item 1.05 without a text query
    response = client.get(
        "/search",
        params={"forms": "8-K", "items": "1.05", "date_from": "2024-01-01", "date_to": "2024-03-31", "page_size": 20},
    )
    assert response.status_code == 200
    item_page = response.json()
    assert item_page["total"] > 0
    assert all("1.05" in result["items"] for result in item_page["results"])

    # ticker scoping resolves through the reference map
    response = client.get("/search", params={"q": "supply chain", "id": "AAPL", "page_size": 10})
    assert response.status_code == 200
    apple = response.json()
    assert apple["total"] > 0
    assert all(result["cik"] == "0000320193" for result in apple["results"])

    # unknown ticker -> 404 (resolves via the ticker reference fetch, a fixtured request)
    response = client.get("/search", params={"q": "x", "id": "ZZZZZZZZ"})
    assert response.status_code == 404

    golden("search", "cybersecurity_8k_page", page1)


def test_search_param_validation(client: TestClient) -> None:
    # neither q nor items
    response = client.get("/search")
    assert response.status_code == 422
    assert "items" in response.json()["detail"]

    # inverted date range
    response = client.get("/search", params={"q": "x", "date_from": "2024-06-30", "date_to": "2024-01-01"})
    assert response.status_code == 422

    # EFTS result window guard (empirical cap: from + size <= 10000)
    response = client.get("/search", params={"q": "x", "start": 9999, "page_size": 100})
    assert response.status_code == 422
    assert "result window" in response.json()["detail"].lower()
