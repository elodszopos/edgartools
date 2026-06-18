#!/usr/bin/env bash
# openapi.json -> ts/src/generated/zod.ts via orval (D1, plan U03)
set -euo pipefail
TS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../ts" && pwd)"
cd "$TS_DIR"
bun run generate
