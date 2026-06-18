#!/usr/bin/env bash
# Self-contained launcher for the edgar-sidecar overnight loop. Zero prerequisites.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Respect a pre-set SEC identity (SEC_EDGAR_USER_AGENT, then EDGAR_IDENTITY); fall back to the bundled contact for a bare launch.
export SEC_EDGAR_USER_AGENT="${SEC_EDGAR_USER_AGENT:-${EDGAR_IDENTITY:-KnowledgeDistiller contact@kdsys.dev}}"
export EDGAR_RATE_LIMIT_PER_SEC="${EDGAR_RATE_LIMIT_PER_SEC:-8}"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-300000}"

exec claude "/loop Read .claude/plans/edgar-sidecar.md and execute exactly one next unit per its Session Protocol."
