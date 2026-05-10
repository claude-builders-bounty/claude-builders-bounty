#!/bin/bash
# CHANGELOG Generator — Claude Code Skill Entry Point
# Usage: bash changelog.sh [--since <tag>] [--output CHANGELOG.md]

set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=""
for cmd in python3 python python3.12 python3.11; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python not found. Install Python 3.10+."
    exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/changelog.py" "$@"
