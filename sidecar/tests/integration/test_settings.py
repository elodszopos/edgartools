"""Integration: apply_settings pushes parsed config into edgartools' live HTTP manager.

HTTP_MGR builds its throttle eagerly at import, so pinning EDGAR_RATE_LIMIT_PER_SEC after
boot would be ignored. apply_settings must reconfigure the LIVE limiter. This touches the
process-global HTTP_MGR (infra) -- hence integration -- and restores it afterward.
"""

from __future__ import annotations

import os
from pathlib import Path

from edgar import is_using_local_storage
from edgar.httpclient import HTTP_MGR, set_rate_limit

from app.settings import Settings, apply_settings


def _current_limit() -> int:
    return HTTP_MGR.rate_limiter.buckets()[0].rates[0].limit


def test_apply_settings_reconfigures_live_rate_limit() -> None:
    original_limit = _current_limit()
    original_env = os.environ.get("EDGAR_RATE_LIMIT_PER_SEC")
    try:
        apply_settings(
            Settings(
                sec_edgar_user_agent="edgar-sidecar tests test@example.com",
                rate_limit_per_sec=original_limit + 1,
                local_data_dir=None,
                use_local_data=False,
            )
        )
        # the live limiter (not just the env var) now carries the configured rate
        assert _current_limit() == original_limit + 1
        assert HTTP_MGR.request_per_sec_limit == original_limit + 1
    finally:
        set_rate_limit(original_limit)
        if original_env is None:
            os.environ.pop("EDGAR_RATE_LIMIT_PER_SEC", None)
        else:
            os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = original_env
    assert _current_limit() == original_limit


def test_apply_settings_governs_local_storage(tmp_path: Path) -> None:
    # parsed EDGAR_LOCAL_DATA_DIR + EDGAR_USE_LOCAL_DATA must actually drive edgartools'
    # storage (the bug: apply_settings parsed them but applied neither). Real edgar calls,
    # real effect asserted. Full env snapshot/restore keeps the global state clean for the
    # rest of the session (set_local_storage_path / use_local_storage mutate process env).
    original_limit = _current_limit()
    env_snapshot = dict(os.environ)
    data_dir = tmp_path / "edgar-store"
    data_dir.mkdir()
    try:
        apply_settings(
            Settings(
                sec_edgar_user_agent="edgar-sidecar tests test@example.com",
                rate_limit_per_sec=original_limit,
                local_data_dir=str(data_dir),
                use_local_data=True,
            )
        )
        assert is_using_local_storage() is True
        assert Path(os.environ["EDGAR_LOCAL_DATA_DIR"]).resolve() == data_dir.resolve()
    finally:
        set_rate_limit(original_limit)
        os.environ.clear()
        os.environ.update(env_snapshot)
    assert _current_limit() == original_limit
    assert is_using_local_storage() is False
