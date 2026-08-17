#!/usr/bin/env bash
# changelog.sh — Fast Changelog Generator Wrapper
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 &>/dev/null; then
    python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
elif command -v python &>/dev/null; then
    python "$SCRIPT_DIR/generate_changelog.py" "$@"
else
    echo "[ERROR] Python 3 is required to run generate_changelog.py" >&2
    exit 1
fi
