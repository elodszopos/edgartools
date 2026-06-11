"""Wiring test: registered handlers turn mapped exceptions into ``{detail}`` JSON responses."""

import httpx
from edgar.httprequests import TooManyRequestsError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import register_exception_handlers


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
