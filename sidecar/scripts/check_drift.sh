#!/usr/bin/env bash
# Drift gate: regenerate openapi.json + zod, fail on any diff vs committed copies, then bun test.
# Also guards committed TS goldens stay in sync and serialization stays hash-seed independent.
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

# Serialization-sensitive unit tests must be PYTHONHASHSEED-independent: dict/set iteration order
# must never leak into the wire (openapi snapshot) or coercer output. Run under two seeds; any
# difference in outcome fails.
SEED_TESTS="tests/unit/test_serialize.py tests/unit/test_openapi_snapshot.py"
set +e
SEED0_OUT="$(PYTHONHASHSEED=0 uv run pytest $SEED_TESTS -q -p no:cacheprovider 2>&1)"; SEED0_RC=$?
SEED1_OUT="$(PYTHONHASHSEED=1 uv run pytest $SEED_TESTS -q -p no:cacheprovider 2>&1)"; SEED1_RC=$?
set -e
# compare the outcome line with the run-to-run-variable duration stripped
SEED0_SUM="$(printf '%s\n' "$SEED0_OUT" | tail -n 1 | sed -E 's/ in [0-9.]+s.*$//')"
SEED1_SUM="$(printf '%s\n' "$SEED1_OUT" | tail -n 1 | sed -E 's/ in [0-9.]+s.*$//')"
if [[ "$SEED0_RC" -ne 0 || "$SEED1_RC" -ne 0 || "$SEED0_SUM" != "$SEED1_SUM" ]]; then
  echo "HASHSEED DRIFT: serialization tests are not PYTHONHASHSEED-independent" >&2
  echo "  seed=0 (rc=$SEED0_RC): $SEED0_SUM" >&2
  echo "  seed=1 (rc=$SEED1_RC): $SEED1_SUM" >&2
  exit 1
fi

# bun test validates every committed golden against the generated Zod (TS leg of the parity gate)
( cd ts && bun test )

# After the bun run the committed TS goldens must be clean -- any untracked or modified fixture
# means a generated artifact was left uncommitted (drift).
FIXTURE_DIRT="$(git status --porcelain -- ts/fixtures/)"
if [[ -n "$FIXTURE_DIRT" ]]; then
  echo "DRIFT: ts/fixtures/ has uncommitted generated goldens (commit or revert them):" >&2
  printf '%s\n' "$FIXTURE_DIRT" >&2
  exit 1
fi
