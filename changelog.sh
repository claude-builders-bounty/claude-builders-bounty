#!/usr/bin/env bash
# ==============================================================================
# changelog.sh — Generate a structured CHANGELOG from git history
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN=""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3 is required to run changelog generator." >&2
    exit 1
fi

"$PYTHON_BIN" "$SCRIPT_DIR/generate_changelog.py" "$@"
