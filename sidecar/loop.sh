#!/usr/bin/env bash
# Self-contained launcher for the edgar-sidecar overnight loop. Zero prerequisites.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export SEC_EDGAR_USER_AGENT="KnowledgeDistiller contact@kdsys.dev"
export EDGAR_RATE_LIMIT_PER_SEC="${EDGAR_RATE_LIMIT_PER_SEC:-8}"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-300000}"

exec claude "/loop Read .claude/plans/edgar-sidecar.md and execute exactly one next unit per its Session Protocol."
