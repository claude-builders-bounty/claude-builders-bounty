#!/usr/bin/env bash
# changelog.sh - Automatically generate structured CHANGELOG.md from git history
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 &>/dev/null; then
    python3 "${SCRIPT_DIR}/generate_changelog.py" "$@"
elif command -v python &>/dev/null; then
    python "${SCRIPT_DIR}/generate_changelog.py" "$@"
else
    echo "Error: Python 3 is required to run changelog generator." >&2
    exit 1
fi
