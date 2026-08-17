#!/usr/bin/env bash
# pre_tool_use.sh — Claude Code Pre-Tool-Use Hook Wrapper
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 &>/dev/null; then
    exec python3 "$SCRIPT_DIR/pre_tool_use.py" "$@"
elif command -v python &>/dev/null; then
    exec python "$SCRIPT_DIR/pre_tool_use.py" "$@"
else
    echo "[ERROR] Python 3 is required for destructive command security hook." >&2
    exit 1
fi
