"""Unit tests for the exception -> HTTP status mapping (pure function only)."""

import asyncio

import httpx
import pytest
from edgar import DataObjectException, Filing
from edgar.core import TooManyRequestsException
from edgar.dates import InvalidDateException
from edgar.entity.core import CompanyNotFoundError
from edgar.enums import ValidationError as EdgarValidationError
from edgar.httprequests import IdentityNotSetException, TooManyRequestsError
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.errors import _handle, format_validation_errors, retry_after_header, status_for_exception


def _must_map(exc: Exception) -> tuple[int, str]:
    mapped = status_for_exception(exc)
    assert mapped is not None, f"expected a mapping for {type(exc).__name__}"
    return mapped


def _http_status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://www.sec.gov/cgi-bin/browse-edgar")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


def test_sec_404_maps_to_404():
    status, detail = _must_map(_http_status_error(404))
    assert status == 404
    assert "sec.gov" in detail


def test_sec_429_status_maps_to_429():
    status, detail = _must_map(_http_status_error(429))
    assert status == 429
    assert detail == "SEC rate limit hit; retry later"


def test_sec_5xx_maps_to_502():
    status, detail = _must_map(_http_status_error(503))
    assert status == 502
    assert "503" in detail


def test_timeout_maps_to_502():
    status, detail = _must_map(httpx.ConnectTimeout("timed out"))
    assert status == 502
    assert "ConnectTimeout" in detail


def test_too_many_requests_error_maps_to_429():
    status, _ = _must_map(TooManyRequestsError("https://www.sec.gov/x", retry_after=600))
    assert status == 429


def test_too_many_requests_exception_maps_to_429():
    status, _ = _must_map(TooManyRequestsException("blocked"))
    assert status == 429


def test_identity_unset_maps_to_503():
    status, detail = _must_map(IdentityNotSetException("User-Agent identity is not set"))
    assert status == 503
    assert "identity" in detail.lower()


def test_invalid_date_maps_to_422():
    status, detail = _must_map(InvalidDateException("Invalid date 2024-13-01"))
    assert status == 422
    assert "2024-13-01" in detail


def test_edgar_validation_error_maps_to_422():
    exc = EdgarValidationError("Invalid form 'XX-K'", parameter="form", invalid_value="XX-K", suggestions=["10-K"])
    status, detail = _must_map(exc)
    assert status == 422
    assert "XX-K" in detail


def test_data_object_exception_maps_to_502():
    filing = Filing(cik=320193, company="Apple Inc.", form="10-K", filing_date="2024-11-01", accession_no="0000320193-24-000123")
    status, detail = _must_map(DataObjectException(filing))
    assert status == 502
    assert "0000320193-24-000123" in detail


def test_company_not_found_maps_to_404_with_suggestions():
    error = CompanyNotFoundError("APPL", suggestions=[{"ticker": "AAPL", "company": "Apple Inc."}])
    status, detail = _must_map(error)
    assert status == 404
    assert "Company not found: 'APPL'" in detail
    assert "'AAPL' (Apple Inc.)" in detail


def test_unknown_exception_is_unmapped():
    assert status_for_exception(KeyError("boom")) is None


def test_retry_after_from_edgar_native_rate_limit():
    assert retry_after_header(TooManyRequestsError("https://www.sec.gov/x", retry_after=600)) == "600"


def test_retry_after_from_httpx_429_response_header():
    # the SEC's Retry-After rides on the httpx response, not as an exception attribute
    request = httpx.Request("GET", "https://www.sec.gov/x")
    response = httpx.Response(429, headers={"Retry-After": "120"}, request=request)
    exc = httpx.HTTPStatusError("HTTP 429", request=request, response=response)
    assert retry_after_header(exc) == "120"


def test_retry_after_absent_on_httpx_429_without_header():
    assert retry_after_header(_http_status_error(429)) is None


def test_retry_after_none_for_unrelated_exception():
    assert retry_after_header(KeyError("boom")) is None


def test_handler_reraises_unmapped_exception_types():
    # drift guard for _handle's re-raise branch: a type without a status mapping must
    # surface as the original exception (FastAPI 500), never a swallowed JSON response
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    with pytest.raises(KeyError):
        asyncio.run(_handle(request, KeyError("boom")))


def test_validation_errors_flatten_to_canonical_detail():
    exc = RequestValidationError(
        [
            {"loc": ("query", "page_size"), "msg": "Input should be greater than or equal to 1"},
            {"loc": ("query", "year"), "msg": "Input should be a valid integer"},
        ]
    )
    assert format_validation_errors(exc) == (
        "query.page_size: Input should be greater than or equal to 1; query.year: Input should be a valid integer"
    )


def test_validation_errors_flatten_handles_empty_list():
    assert format_validation_errors(RequestValidationError([])) == "request validation failed"
