"""The committed openapi.json must match what the app currently produces."""

from scripts.export_openapi import OPENAPI_PATH, render_spec


def test_openapi_snapshot_matches_app():
    assert OPENAPI_PATH.exists(), "openapi.json missing; run: uv run python -m scripts.export_openapi"
    committed = OPENAPI_PATH.read_text(encoding="utf-8")
    assert committed == render_spec(), "openapi.json drifted; regenerate: uv run python -m scripts.export_openapi"
