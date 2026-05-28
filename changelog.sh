#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Thin shell wrapper around changelog.py.
# Usage:
#   bash changelog.sh              # Last tag → HEAD
#   bash changelog.sh --since v1.0.0
#   bash changelog.sh --since 2025-01-01 --until 2025-06-30
#   bash changelog.sh --output CHANGELOG.md --version 1.2.3
#

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# Locate changelog.py (same directory as this script)
PYTHON_SCRIPT="$DIR/changelog.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: changelog.py not found next to this script." >&2
    echo "Expected at: $PYTHON_SCRIPT" >&2
    exit 1
fi

# Run with Python 3
exec python3 "$PYTHON_SCRIPT" "$@"
