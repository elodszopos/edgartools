"""Integration: /filings (quarterly index) and /filings/current (getcurrent feed).

One VCR test per endpoint: the quarterly index download is the expensive interaction, so
every index-touching scenario shares a single cassette. The disk HTTP cache judges
freshness from the RECORDED Date header (index TTL: 30 min), so once a cassette ages
past that, repeat index reads re-hit VCR - hence allow_playback_repeats.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

WINDOW = {"date_from": "2025-01-06", "date_to": "2025-01-10"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.vcr(allow_playback_repeats=True)
def test_filings_index_paging_and_filters(client: TestClient, golden) -> None:
    # page 1 of 10-K filings in a one-week window
    response = client.get("/filings", params={**WINDOW, "form": "10-K", "page_size": 5})
    assert response.status_code == 200
    page1 = response.json()
    assert page1["start"] == 0
    assert page1["page_size"] == 5
    assert len(page1["filings"]) == 5
    assert page1["total"] > 5
    assert page1["has_more"] is True
    assert page1["next_start"] == 5
    for ref in page1["filings"]:
        assert ref["form"] in ("10-K", "10-K/A")  # amendments included by default
        assert WINDOW["date_from"] <= ref["filing_date"] <= WINDOW["date_to"]
        assert len(ref["cik"]) == 10

    # ground truth pinned from the recorded 2025 Q1 index (verified against EDGAR)
    assert page1["total"] == 11
    assert page1["filings"][0] == {
        "accession_number": "0001493152-25-001787",
        "form": "10-K",
        "cik": "0000715446",
        "company": "Anixa Biosciences Inc",
        "filing_date": "2025-01-10",
    }

    # page 2 continues without overlap
    response = client.get("/filings", params={**WINDOW, "form": "10-K", "page_size": 5, "start": 5})
    assert response.status_code == 200
    page2 = response.json()
    assert page2["start"] == 5
    accessions1 = {ref["accession_number"] for ref in page1["filings"]}
    accessions2 = {ref["accession_number"] for ref in page2["filings"]}
    assert accessions1.isdisjoint(accessions2)

    # amendments excluded on request
    response = client.get("/filings", params={**WINDOW, "form": "10-K", "amendments": False, "page_size": 100})
    assert response.status_code == 200
    assert all(ref["form"] == "10-K" for ref in response.json()["filings"])

    # cik filter (Apple) on the same window, any form
    response = client.get("/filings", params={**WINDOW, "id": "320193"})
    assert response.status_code == 200
    apple = response.json()
    assert apple["total"] >= 1
    assert all(ref["cik"] == "0000320193" for ref in apple["filings"])
    assert all("Apple" in ref["company"] for ref in apple["filings"])

    # ticker filter resolves through the SEC ticker map
    response = client.get("/filings", params={**WINDOW, "id": "AAPL"})
    assert response.status_code == 200
    assert {ref["accession_number"] for ref in response.json()["filings"]} == {ref["accession_number"] for ref in apple["filings"]}

    golden("filings", "tenk_window_page", page1)


@pytest.mark.vcr
def test_current_filings_page_and_form_filter(client: TestClient, golden) -> None:
    response = client.get("/filings/current", params={"page_size": 10})
    assert response.status_code == 200
    page = response.json()
    assert page["start"] == 0
    assert page["page_size"] == 10
    assert len(page["filings"]) == 10  # the live feed always has >10 entries
    assert page["has_more"] is True
    assert page["next_start"] == 10
    for ref in page["filings"]:
        assert len(ref["cik"]) == 10
        # wire datetimes are UTC: trailing Z, never a zone offset
        assert ref["accepted"].endswith("Z")

    # ground truth pinned from the recorded feed: -04:00 acceptance normalized to UTC
    assert page["filings"][0]["accepted"] == "2026-06-12T01:59:17Z"
    assert page["filings"][0]["accession_number"] == "0001104659-26-073099"

    # form filter: only Form 4 (and amendments) survive
    response = client.get("/filings/current", params={"form": "4", "page_size": 40})
    assert response.status_code == 200
    form4 = response.json()
    assert len(form4["filings"]) > 0
    assert all(ref["form"] in ("4", "4/A") for ref in form4["filings"])

    golden("filings_current", "first_page", page)


def test_filings_param_validation(client: TestClient) -> None:
    # open-ended date range is rejected (would expand to every index since 1994)
    response = client.get("/filings", params={"date_from": "2025-01-06"})
    assert response.status_code == 422
    assert "together" in response.json()["detail"]

    # year/quarter and dates are mutually exclusive
    response = client.get("/filings", params={**WINDOW, "year": 2025})
    assert response.status_code == 422

    # inverted range
    response = client.get("/filings", params={"date_from": "2025-01-10", "date_to": "2025-01-06"})
    assert response.status_code == 422

    # current: page_size must be one of the SEC-supported sizes
    response = client.get("/filings/current", params={"page_size": 33})
    assert response.status_code == 422

    # current: owner enum enforced
    response = client.get("/filings/current", params={"owner": "everyone"})
    assert response.status_code == 422
