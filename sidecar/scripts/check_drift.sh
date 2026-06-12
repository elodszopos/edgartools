#!/usr/bin/env bash
# Drift gate: regenerate openapi.json + zod, fail on any diff vs committed copies, then bun test.
set -euo pipefail
SIDECAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SIDECAR_DIR"

uv run python -m scripts.export_openapi
scripts/generate_zod.sh

# regen output must match the staged/committed copies; untracked = forgotten to stage
MODIFIED="$(git diff --name-only -- openapi.json ts/src/generated)"
UNTRACKED="$(git ls-files --others --exclude-standard -- openapi.json ts/src/generated)"
if [[ -n "$MODIFIED$UNTRACKED" ]]; then
  echo "DRIFT: regenerated artifacts differ from staged copies:" >&2
  printf '%s\n' "$MODIFIED" "$UNTRACKED" >&2
  git diff -- openapi.json ts/src/generated >&2
  exit 1
fi

cd ts && bun test
