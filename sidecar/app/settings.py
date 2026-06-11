"""Runtime configuration for edgar-sidecar.

Env vars:
    SEC_EDGAR_USER_AGENT      required     SEC identity; boot fails without it
    EDGAR_RATE_LIMIT_PER_SEC  default 8    edgartools-native throttle (edgar/httpclient.py reads it)
    EDGAR_PORT                default 8000 uvicorn bind port (consumed by Dockerfile/launcher, not app code)
    EDGAR_LOCAL_DATA_DIR      optional     edgartools disk cache location (read natively by edgar.paths)
    EDGAR_USE_LOCAL_DATA      optional     edgartools local storage mode (read natively by edgar)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from edgar import set_identity

DEFAULT_RATE_LIMIT_PER_SEC = 8

_TRUTHY = ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    sec_edgar_user_agent: str
    rate_limit_per_sec: int
    local_data_dir: str | None
    use_local_data: bool


def load_settings() -> Settings:
    user_agent = os.environ.get("SEC_EDGAR_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError(
            "SEC_EDGAR_USER_AGENT is not set. The sidecar refuses to start without an SEC identity (see https://www.sec.gov/os/accessing-edgar-data)."
        )

    rate_limit_raw = os.environ.get("EDGAR_RATE_LIMIT_PER_SEC", str(DEFAULT_RATE_LIMIT_PER_SEC))
    try:
        rate_limit = int(rate_limit_raw)
    except ValueError as exc:
        raise RuntimeError(f"EDGAR_RATE_LIMIT_PER_SEC must be an integer, got {rate_limit_raw!r}") from exc
    if rate_limit < 1:
        raise RuntimeError(f"EDGAR_RATE_LIMIT_PER_SEC must be >= 1, got {rate_limit}")

    return Settings(
        sec_edgar_user_agent=user_agent,
        rate_limit_per_sec=rate_limit,
        local_data_dir=os.environ.get("EDGAR_LOCAL_DATA_DIR") or None,
        use_local_data=os.environ.get("EDGAR_USE_LOCAL_DATA", "").strip().lower() in _TRUTHY,
    )


def apply_settings(settings: Settings) -> None:
    # throttle env must be pinned before edgartools lazily creates its HTTP clients
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = str(settings.rate_limit_per_sec)
    set_identity(settings.sec_edgar_user_agent)
