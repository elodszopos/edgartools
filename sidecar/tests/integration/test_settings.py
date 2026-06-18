"""Integration: the sidecar pins the SEC throttle into the env before edgartools imports, and
apply_settings pushes identity + local-storage config into edgartools.

EDGAR_RATE_LIMIT_PER_SEC is read by edgartools' HTTP_MGR exactly once, at import; app/__init__
pins the sidecar default ahead of that import (edgartools' own default differs). These tests touch
process-global state (env + edgartools storage) -- hence integration -- and restore it afterward.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from edgar import is_using_local_storage
from edgar.httpclient import get_edgar_rate_limit_per_sec

from app import DEFAULT_RATE_LIMIT_PER_SEC
from app.settings import Settings, apply_settings, load_settings

_SIDECAR_ROOT = Path(__file__).resolve().parents[2]


def test_app_package_pins_default_rate_limit_when_unset() -> None:
    # With EDGAR_RATE_LIMIT_PER_SEC unset, importing the app package must pin the sidecar default
    # into the env. This runs before edgartools imports, so HTTP_MGR builds its throttle at the
    # sidecar's rate (edgartools' own default is 9). Checked in a clean subprocess because the env
    # and edgartools' import are process-global and already settled in this session.
    env = {k: v for k, v in os.environ.items() if k != "EDGAR_RATE_LIMIT_PER_SEC"}
    result = subprocess.run(
        [sys.executable, "-c", "import os, app; print(os.environ['EDGAR_RATE_LIMIT_PER_SEC'])"],
        capture_output=True,
        text=True,
        env=env,
        cwd=_SIDECAR_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(DEFAULT_RATE_LIMIT_PER_SEC)


def test_edgar_builds_throttle_from_rate_limit_env() -> None:
    # The pin works because edgartools derives its throttle from EDGAR_RATE_LIMIT_PER_SEC at import.
    # Verify edgartools honors the env var -- the contract the app/__init__ pin depends on.
    snapshot = os.environ.get("EDGAR_RATE_LIMIT_PER_SEC")
    try:
        os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "11"
        assert get_edgar_rate_limit_per_sec() == 11
    finally:
        if snapshot is None:
            os.environ.pop("EDGAR_RATE_LIMIT_PER_SEC", None)
        else:
            os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = snapshot


def test_apply_settings_governs_local_storage(tmp_path: Path) -> None:
    # parsed EDGAR_LOCAL_DATA_DIR + EDGAR_USE_LOCAL_DATA must actually drive edgartools' storage.
    # Real edgar calls, real effect asserted. Full env snapshot/restore keeps global state clean for
    # the rest of the session (set_local_storage_path / use_local_storage mutate process env).
    env_snapshot = dict(os.environ)
    data_dir = tmp_path / "edgar-store"
    data_dir.mkdir()
    try:
        apply_settings(
            Settings(
                sec_edgar_user_agent="edgar-sidecar tests test@example.com",
                rate_limit_per_sec=DEFAULT_RATE_LIMIT_PER_SEC,
                local_data_dir=str(data_dir),
                use_local_data=True,
            )
        )
        assert is_using_local_storage() is True
        assert Path(os.environ["EDGAR_LOCAL_DATA_DIR"]).resolve() == data_dir.resolve()
    finally:
        os.environ.clear()
        os.environ.update(env_snapshot)
    assert is_using_local_storage() is False


def test_load_settings_missing_user_agent_raises() -> None:
    snapshot = dict(os.environ)
    try:
        os.environ.pop("SEC_EDGAR_USER_AGENT", None)
        with pytest.raises(RuntimeError, match="SEC_EDGAR_USER_AGENT is not set"):
            load_settings()
    finally:
        os.environ.clear()
        os.environ.update(snapshot)


def test_load_settings_non_integer_rate_limit_raises() -> None:
    snapshot = dict(os.environ)
    try:
        os.environ["SEC_EDGAR_USER_AGENT"] = "edgar-sidecar tests test@example.com"
        os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "abc"
        with pytest.raises(RuntimeError, match=r"EDGAR_RATE_LIMIT_PER_SEC must be an integer, got 'abc'"):
            load_settings()
    finally:
        os.environ.clear()
        os.environ.update(snapshot)


def test_load_settings_sub_minimum_rate_limit_raises() -> None:
    snapshot = dict(os.environ)
    try:
        os.environ["SEC_EDGAR_USER_AGENT"] = "edgar-sidecar tests test@example.com"
        for bad in ("0", "-3"):
            os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = bad
            with pytest.raises(RuntimeError, match=rf"EDGAR_RATE_LIMIT_PER_SEC must be >= 1, got {bad}"):
                load_settings()
    finally:
        os.environ.clear()
        os.environ.update(snapshot)


def test_apply_settings_missing_local_storage_path_raises(tmp_path: Path) -> None:
    # A non-existent local-storage dir must fail loudly, not silently no-op. Snapshot/restore env
    # since set_identity runs before the raise.
    env_snapshot = dict(os.environ)
    missing = tmp_path / "does-not-exist"
    try:
        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            apply_settings(
                Settings(
                    sec_edgar_user_agent="edgar-sidecar tests test@example.com",
                    rate_limit_per_sec=DEFAULT_RATE_LIMIT_PER_SEC,
                    local_data_dir=str(missing),
                    use_local_data=True,
                )
            )
    finally:
        os.environ.clear()
        os.environ.update(env_snapshot)
    assert is_using_local_storage() is False
