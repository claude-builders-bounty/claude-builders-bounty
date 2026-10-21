#!/usr/bin/env bash
# Generate structured CHANGELOG from git history
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: python3 is required but not found in PATH" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/bin/generate-changelog" "$@"
