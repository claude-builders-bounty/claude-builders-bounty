#!/usr/bin/env bash
set -euo pipefail

# changelog.sh - Shell wrapper for generate-changelog
VERSION="${1:-Unreleased}"
OUTPUT="${2:-CHANGELOG.md}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 &>/dev/null; then
    python3 "${SCRIPT_DIR}/generate-changelog.py" --version "$VERSION" --output "$OUTPUT"
elif command -v python &>/dev/null; then
    python "${SCRIPT_DIR}/generate-changelog.py" --version "$VERSION" --output "$OUTPUT"
else
    echo "Error: Python 3 is required to run generate-changelog." >&2
    exit 1
fi
