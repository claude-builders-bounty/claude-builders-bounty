#!/usr/bin/env bash
# CHANGELOG Generator — bash wrapper for Python script
# Usage: bash changelog.sh [--since <tag>] [--output <file>] [--unreleased]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/changelog.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: changelog.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

python3 "$PYTHON_SCRIPT" "$@"