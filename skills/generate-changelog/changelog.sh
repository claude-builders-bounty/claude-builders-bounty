#!/usr/bin/env bash
# Structured CHANGELOG.md Generator (claude-builders-bounty/claude-builders-bounty#1)
# Usage: bash changelog.sh [--repo <path>] [--output <CHANGELOG.md>] [--since-tag <tag>]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "${SCRIPT_DIR}/changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "${SCRIPT_DIR}/changelog.py" "$@"
else
    echo "Error: python3 or python is required to run changelog.sh" >&2
    exit 1
fi
