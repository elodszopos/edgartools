"""Export the app's OpenAPI spec to sidecar/openapi.json (committed snapshot).

Run from sidecar/: uv run python -m scripts.export_openapi
"""

import json
from pathlib import Path

from app.main import app

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def render_spec() -> str:
    # app.openapi() is deterministic for a given app; no timestamps, stable key order
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    rendered = render_spec()
    OPENAPI_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {OPENAPI_PATH} ({len(rendered)} bytes)")  # noqa: T201


if __name__ == "__main__":
    main()
