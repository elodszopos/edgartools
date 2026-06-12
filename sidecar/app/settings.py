"""Runtime configuration for edgar-sidecar.

Env vars (parsed by load_settings, then pushed into edgartools by apply_settings):
    SEC_EDGAR_USER_AGENT      required     SEC identity; boot fails without it (-> set_identity)
    EDGAR_RATE_LIMIT_PER_SEC  default 8    SEC request throttle (-> set_rate_limit reconfigures the live limiter)
    EDGAR_PORT                default 8000 uvicorn bind port (consumed by Dockerfile/launcher, not app code)
    EDGAR_LOCAL_DATA_DIR      optional     edgartools data dir (-> set_local_storage_path)
    EDGAR_USE_LOCAL_DATA      optional     enable edgartools local storage when truthy (-> use_local_storage)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from edgar import set_identity, set_local_storage_path, set_rate_limit, use_local_storage

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
    set_identity(settings.sec_edgar_user_agent)
    # HTTP_MGR builds its throttle eagerly at import from EDGAR_RATE_LIMIT_PER_SEC, before this
    # runs - so mutating the env var alone is too late. Reconfigure the live limiter instead.
    set_rate_limit(settings.rate_limit_per_sec)
    # Point edgartools at the configured data dir, then enable local storage when requested.
    # Enable-only: never disable here (edgar truthy-checks the raw EDGAR_USE_LOCAL_DATA in
    # places, so writing the "0" sentinel would read back as on).
    if settings.local_data_dir is not None:
        set_local_storage_path(settings.local_data_dir)
    if settings.use_local_data:
        use_local_storage(True)
