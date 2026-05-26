#!/usr/bin/env bash
#
# changelog.sh — Generate CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh                    # Generate in current dir
#   bash changelog.sh --output CHANGELOG.md
#   bash changelog.sh --since v1.0.0
#   bash changelog.sh --repo /path/to/project
#
# Requires: python3, git
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Locate changelog.py — same directory as this script, or PATH
CHANGELOG_PY="${SCRIPT_DIR}/changelog.py"

if [ ! -f "$CHANGELOG_PY" ]; then
    # Try PATH
    CHANGELOG_PY="$(command -v changelog.py || true)"
fi

if [ -z "$CHANGELOG_PY" ] || [ ! -f "$CHANGELOG_PY" ]; then
    echo "❌ Error: changelog.py not found next to changelog.sh or in PATH." >&2
    echo "   Place both files in the same directory, or install changelog.py in your PATH." >&2
    exit 1
fi

# Check dependencies
if ! command -v python3 &>/dev/null; then
    echo "❌ Error: python3 is required but not found in PATH." >&2
    exit 1
fi

if ! command -v git &>/dev/null; then
    echo "❌ Error: git is required but not found in PATH." >&2
    exit 1
fi

python3 "$CHANGELOG_PY" "$@"
