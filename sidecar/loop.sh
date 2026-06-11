#!/usr/bin/env bash
# Self-contained launcher for the edgar-sidecar overnight loop.
# Only human prerequisite: 1Password CLI unlocked (op may prompt biometric at launch).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export SEC_EDGAR_USER_AGENT="$(op read 'op://api_creds/sec-edgar/user_agent')"
export EDGAR_RATE_LIMIT_PER_SEC="${EDGAR_RATE_LIMIT_PER_SEC:-8}"

exec claude "/loop Read .claude/plans/edgar-sidecar.md and execute exactly one next unit per its Session Protocol."
