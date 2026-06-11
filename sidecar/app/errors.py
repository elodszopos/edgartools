"""edgartools/httpx exception -> HTTP status mapping (wire: errors are FastAPI ``{detail}``).

Statuses (plan "Wire conventions"): 404 not-found-at-SEC, 422 bad params, 429 SEC limit,
502 edgartools/SEC upstream error, 503 identity unset. Unknown exceptions stay unmapped
and surface as FastAPI's default 500 - programming errors must stay loud.
"""

from __future__ import annotations

import httpx
from edgar import DataObjectException
from edgar.core import TooManyRequestsException
from edgar.dates import InvalidDateException
from edgar.enums import ValidationError as EdgarValidationError
from edgar.httprequests import IdentityNotSetException, TooManyRequestsError
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

RATE_LIMIT_DETAIL = "SEC rate limit hit; retry later"

_HANDLED_TYPES: tuple[type[Exception], ...] = (
    TooManyRequestsError,
    TooManyRequestsException,
    IdentityNotSetException,
    InvalidDateException,
    EdgarValidationError,
    DataObjectException,
    httpx.HTTPError,
)


def status_for_exception(exc: Exception) -> tuple[int, str] | None:
    """Return (status, detail) for exceptions the sidecar owns, None for everything else."""
    if isinstance(exc, (TooManyRequestsError, TooManyRequestsException)):
        return 429, RATE_LIMIT_DETAIL
    if isinstance(exc, IdentityNotSetException):
        return 503, "SEC identity not set; service starting or misconfigured"
    if isinstance(exc, (InvalidDateException, EdgarValidationError)):
        return 422, str(exc)
    if isinstance(exc, DataObjectException):
        return 502, str(exc)
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 404:
            return 404, f"not found at SEC: {exc.request.url}"
        if status == 429:
            return 429, RATE_LIMIT_DETAIL
        return 502, f"SEC upstream returned {status} for {exc.request.url}"
    if isinstance(exc, httpx.HTTPError):  # timeouts, transport and protocol errors
        return 502, f"SEC upstream error: {type(exc).__name__}: {exc}"
    return None


async def _handle(request: Request, exc: Exception) -> JSONResponse:
    mapped = status_for_exception(exc)
    if mapped is None:  # registered type without a mapping is a programming error
        raise exc
    status, detail = mapped
    headers: dict[str, str] = {}
    retry_after = getattr(exc, "retry_after", None)
    if status == 429 and retry_after:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse({"detail": detail}, status_code=status, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    for exc_type in _HANDLED_TYPES:
        app.add_exception_handler(exc_type, _handle)
