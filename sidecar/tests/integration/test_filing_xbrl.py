"""Integration: /filing/{accession}/xbrl per-filing statements.

Unlike /company/{id}/financials (which selects the company's latest 10-K/10-Q via the
form chain), this serves the XBRL statements of ONE explicit filing addressed by accession.
Target = NVIDIA FY2025 10-K (0001045810-25-000023, filed 2025-02-26, fiscal year ended
2025-01-26): the enriched accession lookup resolves offline from the recorded 2025 Q1 form
index, so only the filing's own SGML/XBRL is newly recorded. The no-XBRL case reuses the
already-recorded NVIDIA Form 4 (0001045810-25-000002), which carries no XBRL.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_NVDA_10K = "0001045810-25-000023"
_NVDA_FORM4 = "0001045810-25-000002"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _record(statement: dict, concept: str, label: str) -> dict:
    matches = [r for r in statement["records"] if r["concept"] == concept and r["label"] == label]
    assert len(matches) == 1, f"expected exactly one {concept} / {label!r} row, got {len(matches)}"
    return matches[0]


def _values(record: dict) -> list:
    return [v["value"] for v in record["values"]]


def test_filing_xbrl_nvidia_10k(client: TestClient, golden) -> None:
    response = client.get(f"/filing/{_NVDA_10K}/xbrl")
    assert response.status_code == 200
    body = response.json()

    assert body["cik"] == "0001045810"
    assert body["company"] == "NVIDIA CORP"
    assert body["form"] == "10-K"
    assert body["accession_number"] == _NVDA_10K
    assert body["filing_date"] == "2025-02-26"
    assert body["period_of_report"] == "2025-01-26"
    assert body["view"] == "standardized"
    assert body["dimensions"] is False

    income = body["income_statement"]
    assert income is not None
    # three fiscal years, newest first; FY2025 ends on NVIDIA's last-Sunday-of-January year-end
    assert [p["period_end"] for p in income["periods"]] == ["2025-01-26", "2024-01-28", "2023-01-29"]

    # ground truth, hand-verified against the FY2025 10-K: revenue 130,497M / 60,922M / 26,974M
    revenue = _record(income, "us-gaap_Revenues", "Revenue")
    assert _values(revenue) == [130497000000.0, 60922000000.0, 26974000000.0]

    assert body["balance_sheet"] is not None
    assert body["cashflow_statement"] is not None

    golden("filing_xbrl", "nvidia_10k", body)


def test_filing_xbrl_no_xbrl_is_404(client: TestClient) -> None:
    # a Form 4 carries no XBRL statements -> 404, never an empty-statement 200 (silence check)
    response = client.get(f"/filing/{_NVDA_FORM4}/xbrl")
    assert response.status_code == 404
    assert response.json() == {"detail": f"filing {_NVDA_FORM4} has no XBRL data"}


def test_filing_xbrl_nonexistent_is_404(client: TestClient) -> None:
    # 1995 accession keeps the not-found scan in the small early-EDGAR indexes
    response = client.get("/filing/0000000000-95-654321/xbrl")
    assert response.status_code == 404
    assert "0000000000-95-654321" in response.json()["detail"]


def test_filing_xbrl_bad_accession_is_422(client: TestClient) -> None:
    assert client.get("/filing/not-an-accession/xbrl").status_code == 422
