#!/usr/bin/env bash
# changelog.sh — thin portable entrypoint for the generate-changelog skill.
# Usage: bash changelog.sh [--output FILE] [--since TAG] [--repo PATH] [--prepend] [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${SCRIPT_DIR}/scripts/generate.py"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi

exec python3 "$PY" "$@"
