#!/usr/bin/env bash
# changelog.sh — Wrapper script to generate CHANGELOG.md from git log
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3 || echo "python")"

if ! command -v git &> /dev/null; then
    echo "❌ Error: git command not found." >&2
    exit 1
fi

if [ ! -d ".git" ]; then
    echo "⚠️ Warning: Current directory is not a git repository." >&2
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/generate_changelog.py" "$@"
