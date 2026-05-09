#!/usr/bin/env bash
# changelog.sh — thin wrapper around generate_changelog.py so users can
# invoke the tool with the form mandated by the bounty: `bash changelog.sh`.
#
# Forwards every arg through. The Python script is stdlib-only.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY="python"
fi
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "error: Python 3 not found on PATH (set \$PYTHON to override)" >&2
  exit 1
fi

exec "$PY" "$DIR/generate_changelog.py" "$@"
