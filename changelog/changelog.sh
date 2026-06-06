#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh
#
# Requirements: Python 3, git

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

python3 "$SCRIPT_DIR/changelog.py" "$@"
