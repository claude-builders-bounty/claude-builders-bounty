#!/usr/bin/env bash
# changelog.sh — Shell entrypoint for changelog generator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/changelog.py"

if command -v python3 &>/dev/null; then
    exec python3 "${PYTHON_SCRIPT}" "$@"
elif command -v python &>/dev/null; then
    exec python "${PYTHON_SCRIPT}" "$@"
else
    echo "❌ Error: Python 3 is required to run changelog.py" >&2
    exit 1
fi
