"""Opt-in live smoke test: a real round-trip to SEC EDGAR through the full app.

SKIPPED by default (conftest deselects live-marked tests). Runs ONLY with `-m live` or RUN_LIVE=1,
which also makes conftest leave the httpx transports unpatched so these requests reach the real SEC.
One endpoint plus one cheap company lookup -- a smoke test, not a suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.live
def test_live_health_and_company_lookup() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        body = health.json()
        assert body["status"] == "ok"
        assert body["identity_set"] is True
        assert body["edgartools_version"]

        company = client.get("/company/AAPL")
        assert company.status_code == 200
        profile = company.json()
        assert profile["cik"] == "0000320193"
        assert "Apple" in profile["name"]
