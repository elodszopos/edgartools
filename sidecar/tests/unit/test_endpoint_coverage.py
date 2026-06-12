"""Static coverage gates (no SEC, pure source scans):

1. Every app route is exercised by at least one tests/integration/*.py HTTP test.
2. The committed TS golden directories and the goldens.test.ts schema map stay in lockstep
   (fixtures vs endpoints parity for the generated-Zod leg).
"""

from __future__ import annotations

import re
from pathlib import Path

from app.main import app

_SIDECAR = Path(__file__).resolve().parent.parent.parent
_INTEGRATION_DIR = _SIDECAR / "tests" / "integration"
_FIXTURES_DIR = _SIDECAR / "ts" / "fixtures" / "responses"
_GOLDENS_TEST = _SIDECAR / "ts" / "tests" / "goldens.test.ts"

# Routes intentionally NOT covered by a tests/integration/*.py HTTP test, each with a reason.
# Keep MINIMAL -- add a route only when it genuinely has no behavioral integration test.
_COVERAGE_ALLOWLIST: dict[str, str] = {
    "/openapi.json": "schema parity asserted by tests/unit/test_openapi_snapshot.py, not over HTTP",
    "/docs": "FastAPI built-in Swagger UI page; no behavioral contract to integration-test",
    "/docs/oauth2-redirect": "FastAPI built-in OAuth2 redirect helper; no behavioral contract",
    "/redoc": "FastAPI built-in ReDoc UI page; no behavioral contract to integration-test",
}

_PARAM = re.compile(r"\{[^}]+\}")
# a concrete path value (real id/accession) OR an f-string {placeholder}
_VALUE = r"""(?:[^/"'{}\s]+|\{[^}]+\})"""
# trailing boundary keeps /a/{x} distinct from /a/{x}/b so each endpoint must be hit on its own
_BOUNDARY = r"""(?=["'?\s]|$)"""


def _route_pattern(path: str) -> re.Pattern[str]:
    static = [re.escape(seg) for seg in _PARAM.split(path)]
    return re.compile(_VALUE.join(static) + _BOUNDARY)


def _app_route_paths() -> list[str]:
    return sorted({route.path for route in app.routes if isinstance(getattr(route, "path", None), str)})


def _integration_sources() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(_INTEGRATION_DIR.glob("*.py")))


def test_every_route_has_an_integration_test() -> None:
    sources = _integration_sources()
    uncovered = [path for path in _app_route_paths() if path not in _COVERAGE_ALLOWLIST and not _route_pattern(path).search(sources)]
    assert not uncovered, (
        "app routes not exercised by any tests/integration/*.py test (add a test, or only if "
        f"genuinely untestable an allowlist entry with a reason): {uncovered}"
    )


def test_coverage_allowlist_is_clean() -> None:
    routes = set(_app_route_paths())
    sources = _integration_sources()
    for path, reason in _COVERAGE_ALLOWLIST.items():
        assert path in routes, f"allowlisted route {path!r} no longer exists; drop it from the allowlist"
        assert reason.strip(), f"allowlisted route {path!r} needs a one-line reason"
        assert not _route_pattern(path).search(sources), f"allowlisted route {path!r} now HAS an integration test; drop it from the allowlist"


def _fixture_dirs() -> set[str]:
    return {p.name for p in _FIXTURES_DIR.iterdir() if p.is_dir()}


def _goldens_schema_keys() -> set[str]:
    src = _GOLDENS_TEST.read_text(encoding="utf-8")
    block = re.search(r"RESPONSE_SCHEMAS[^=]*=\s*\{(.*?)\};", src, re.DOTALL)
    assert block, "could not locate the RESPONSE_SCHEMAS map in goldens.test.ts"
    return set(re.findall(r"^\s*([A-Za-z0-9_]+)\s*:", block.group(1), re.MULTILINE))


def test_ts_fixture_dirs_match_goldens_schema_map() -> None:
    # bun test only checks dirs-that-exist have a mapping; this also catches a STALE mapping whose
    # fixture dir was removed/renamed, and a fixture dir added without a mapping.
    dirs = _fixture_dirs()
    keys = _goldens_schema_keys()
    assert keys, "parsed no RESPONSE_SCHEMAS keys -- the goldens.test.ts format changed"
    assert not (dirs - keys), f"golden dirs with no Zod schema mapping in goldens.test.ts: {sorted(dirs - keys)}"
    assert not (keys - dirs), f"goldens.test.ts maps endpoints with no committed fixture dir: {sorted(keys - dirs)}"
