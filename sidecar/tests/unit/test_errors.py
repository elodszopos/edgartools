"""Unit tests for the exception -> HTTP status mapping (pure function only)."""

import httpx
from edgar import DataObjectException, Filing
from edgar.core import TooManyRequestsException
from edgar.dates import InvalidDateException
from edgar.enums import ValidationError as EdgarValidationError
from edgar.httprequests import IdentityNotSetException, TooManyRequestsError

from app.errors import status_for_exception


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


def test_unknown_exception_is_unmapped():
    assert status_for_exception(KeyError("boom")) is None
