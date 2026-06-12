"""edgar-sidecar FastAPI application: identity boot + router wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.errors import register_exception_handlers
from app.routers import filings, health, search, tickers
from app.settings import apply_settings, load_settings


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    # load_settings raises without SEC_EDGAR_USER_AGENT -> uvicorn aborts boot
    settings = load_settings()
    apply_settings(settings)
    application.state.settings = settings
    yield


app = FastAPI(
    title="edgar-sidecar",
    summary="HTTP wrapper around edgartools - the single SEC egress",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(health.router)
app.include_router(filings.router)
app.include_router(search.router)
app.include_router(tickers.router)
register_exception_handlers(app)
