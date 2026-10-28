#!/usr/bin/env bash
# changelog.sh - Generate structured CHANGELOG.md from git commits
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3 || echo "python")"

if [ -f "/Users/eiden/hansong/.venv/bin/python" ]; then
    PYTHON_BIN="/Users/eiden/hansong/.venv/bin/python"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/generate_changelog.py" "$@"
