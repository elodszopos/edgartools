"""Integration: /company/{id}/facts (+ /facts/concept/{c}, /facts/search).

Ground truth verified by hand against the recorded SEC companyfacts (CIK0000320193,
recorded 2026-06-12): AAPL FY2024 net sales = $391,035,000,000, reported in the FY2024
10-K (0000320193-24-000123, filed 2024-11-01, period ended 2024-09-28). The companyfacts
API returns a flat (non-dimensional) fact set, so every AAPL fact is is_dimensioned=False;
the Fact model still carries dimensions for sources that populate them.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_REVENUE = "RevenueFromContractWithCustomerExcludingAssessedTax"
_REVENUE_QUALIFIED = f"us-gaap:{_REVENUE}"

# AAPL's total fact count in the recorded companyfacts snapshot (paging ground truth)
_AAPL_TOTAL = 24852

# the first fact in get_all_facts() order is deterministic given the fixed fixture
_FIRST_FACT_CONCEPT = "dei:EntityCommonStockSharesOutstanding"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_facts_first_page(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/facts", params={"page_size": 2})
    assert response.status_code == 200
    body = response.json()

    assert body["cik"] == "0000320193"
    assert body["company"] == "Apple Inc."
    assert body["total"] == _AAPL_TOTAL
    assert body["start"] == 0
    assert body["page_size"] == 2
    assert body["has_more"] is True
    assert body["next_start"] == 2
    assert len(body["facts"]) == 2

    first = body["facts"][0]
    assert first["concept"] == _FIRST_FACT_CONCEPT
    assert first["taxonomy"] == "dei"
    assert first["value"] == 895816758  # raw value preserved as int
    assert first["numeric_value"] == 895816758.0  # calc-ready float
    assert first["unit"] == "shares"
    assert first["fiscal_year"] == 2009
    assert first["fiscal_period"] == "Q3"
    assert first["form_type"] == "10-Q"
    assert first["accession"] == "0001193125-09-153165"
    assert first["is_dimensioned"] is False

    golden("company_facts", "aapl_page", body)


def test_facts_paging_tail(client: TestClient) -> None:
    # last full page: 24852 facts, start at 24850 -> 2 left, no more
    response = client.get("/company/AAPL/facts", params={"start": _AAPL_TOTAL - 2, "page_size": 100})
    assert response.status_code == 200
    body = response.json()
    assert len(body["facts"]) == 2
    assert body["has_more"] is False
    assert body["next_start"] is None

    # start past the end: empty page, never an error
    past = client.get("/company/AAPL/facts", params={"start": _AAPL_TOTAL + 10, "page_size": 50}).json()
    assert past["facts"] == []
    assert past["total"] == _AAPL_TOTAL
    assert past["has_more"] is False
    assert past["next_start"] is None


def test_facts_concept_ground_truth(client: TestClient) -> None:
    # fuzzy (default): substring match on concept OR label, case-insensitive
    response = client.get(f"/company/AAPL/facts/concept/{_REVENUE}", params={"page_size": 200})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 113

    fy2024 = [f for f in body["facts"] if f["fiscal_year"] == 2024 and f["fiscal_period"] == "FY" and f["numeric_value"] == 391035000000.0]
    assert len(fy2024) == 1, "expected exactly one FY2024 net-sales fact"
    # full-fidelity ground truth: every field of AAPL's FY2024 net sales fact
    assert fy2024[0] == {
        "concept": _REVENUE_QUALIFIED,
        "taxonomy": "us-gaap",
        "label": "Revenue from Contract with Customer, Excluding Assessed Tax",
        "value": 391035000000,
        "numeric_value": 391035000000.0,
        "unit": "USD",
        "scale": None,
        "period_start": "2023-10-01",
        "period_end": "2024-09-28",
        "period_type": "duration",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
        "filing_date": "2024-11-01",
        "form_type": "10-K",
        "accession": "0000320193-24-000123",
        "data_quality": "high",
        "is_audited": True,
        "is_restated": False,
        "is_estimated": False,
        "confidence_score": 0.9,
        "semantic_tags": [],
        "business_context": (
            "Amount, excluding tax collected from customer, of revenue from satisfaction of "
            "performance obligation by transferring promised good or service to customer. Tax "
            "collected from customer is tax assessed by governmental authority that is both "
            "imposed on and concurrent with specific revenue-producing transaction, including, "
            "but not limited to, sales, use, value added and excise."
        ),
        "calculation_context": None,
        "context_ref": None,
        "dimensions": None,
        "statement_type": "IncomeStatement",
        "line_item_sequence": None,
        "depth": 2,
        "parent_concept": "IncomeStatementAbstract",
        "section": "Revenue",
        "is_abstract": False,
        "is_total": False,
        "presentation_order": None,
        "is_dimensioned": False,
    }


def test_facts_concept_exact_requires_qualified_name(client: TestClient, golden) -> None:
    # exact matches the indexed concept key, which is taxonomy-qualified
    bare_exact = client.get(f"/company/AAPL/facts/concept/{_REVENUE}", params={"exact": "true"}).json()
    assert bare_exact["total"] == 0  # bare name is not an index key

    qualified_exact = client.get(
        f"/company/AAPL/facts/concept/{_REVENUE_QUALIFIED}",
        params={"exact": "true", "page_size": 2},
    )
    assert qualified_exact.status_code == 200
    qb = qualified_exact.json()
    assert qb["total"] == 113
    assert all(f["concept"] == _REVENUE_QUALIFIED for f in qb["facts"])

    golden("company_facts_concept", "aapl_revenue_exact", qb)


def test_facts_search(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/facts/search", params={"q": "cash", "page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6881
    assert len(body["facts"]) == 2
    # every hit matches the pattern in one of the searched text fields
    for fact in body["facts"]:
        haystack = " ".join(str(fact[k] or "") for k in ("concept", "label", "taxonomy", "business_context", "statement_type")).lower()
        assert "cash" in haystack

    golden("company_facts_search", "aapl_cash", body)


def test_facts_search_regex(client: TestClient) -> None:
    # the pattern is a real regex (case-insensitive): alternation matches either term
    response = client.get("/company/AAPL/facts/search", params={"q": "revenue|inventory", "page_size": 1})
    assert response.status_code == 200
    assert response.json()["total"] > 0


def test_facts_search_bad_regex_is_422(client: TestClient) -> None:
    response = client.get("/company/AAPL/facts/search", params={"q": "("})
    assert response.status_code == 422
    assert "invalid search regex" in response.json()["detail"]


def test_facts_no_facts_is_404(client: TestClient) -> None:
    # CIK0001347842 (an individual) has no XBRL companyfacts -> get_facts() is None
    for path in (
        "/company/0001347842/facts",
        f"/company/0001347842/facts/concept/{_REVENUE}",
        "/company/0001347842/facts/search?q=cash",
    ):
        response = client.get(path)
        assert response.status_code == 404, path
        assert response.json() == {"detail": "no XBRL facts at SEC for CIK 0001347842"}


def test_facts_param_bounds(client: TestClient) -> None:
    assert client.get("/company/AAPL/facts", params={"page_size": 0}).status_code == 422
    assert client.get("/company/AAPL/facts", params={"page_size": 1001}).status_code == 422
    assert client.get("/company/AAPL/facts", params={"start": -1}).status_code == 422
    # search requires q
    assert client.get("/company/AAPL/facts/search").status_code == 422
