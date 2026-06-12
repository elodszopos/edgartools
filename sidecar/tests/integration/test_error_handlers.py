"""Wiring test: registered handlers turn mapped exceptions into ``{detail}`` JSON responses,
plus goldens pinning the canonical ErrorResponse shape per error mechanism."""

import httpx
import pytest
from edgar.httprequests import TooManyRequestsError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import register_exception_handlers
from app.main import app as sidecar_app


def _client_with_failing_route(exc: Exception) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise exc

    return TestClient(app)


def test_rate_limit_handler_sets_status_detail_and_retry_after():
    client = _client_with_failing_route(TooManyRequestsError("https://www.sec.gov/x", retry_after=600))
    response = client.get("/boom")
    assert response.status_code == 429
    assert response.json() == {"detail": "SEC rate limit hit; retry later"}
    assert response.headers["Retry-After"] == "600"


def test_upstream_status_error_becomes_502():
    request = httpx.Request("GET", "https://www.sec.gov/files/x.json")
    response = httpx.Response(503, request=request)
    client = _client_with_failing_route(httpx.HTTPStatusError("HTTP 503", request=request, response=response))
    reply = client.get("/boom")
    assert reply.status_code == 502
    assert "503" in reply.json()["detail"]


@pytest.fixture(scope="module")
def client():
    with TestClient(sidecar_app) as test_client:
        yield test_client


def test_canonical_error_shapes(client: TestClient, golden) -> None:
    """Every error mechanism emits the same ``{detail: str}`` ErrorResponse body."""
    # framework request-validation 422, flattened from pydantic's error list
    response = client.get("/filings", params={"page_size": 0})
    assert response.status_code == 422
    validation = response.json()
    assert validation == {"detail": "query.page_size: Input should be greater than or equal to 1"}

    # route-rule 422 raised as HTTPException
    response = client.get("/filings", params={"date_from": "2025-01-06"})
    assert response.status_code == 422
    param_rule = response.json()
    assert param_rule == {"detail": "date_from and date_to must be provided together"}

    # unknown ticker 404 from the shared resolver (ticker reference is a fixtured fetch)
    response = client.get("/search", params={"q": "x", "id": "ZZZZZZZZ"})
    assert response.status_code == 404
    ticker_404 = response.json()
    assert ticker_404 == {"detail": "ticker 'ZZZZZZZZ' not found in the SEC ticker reference"}

    # CompanyNotFoundError mapped by the exception handler, suggestions included
    response = client.get("/company/ZZZZJUNK")
    assert response.status_code == 404
    company_404 = response.json()
    assert company_404["detail"].startswith("Company not found: 'ZZZZJUNK'")

    golden("errors", "validation_422", validation)
    golden("errors", "param_rule_422", param_rule)
    golden("errors", "ticker_not_found_404", ticker_404)
    golden("errors", "company_not_found_404", company_404)
