#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Destructive Bash Command Blocker
# Exit code 0: Command allowed
# Exit code 1: Command blocked (message printed to stderr)

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PYTHON_BIN="python3"

if ! command -v python3 &> /dev/null; then
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$DIR/pre-tool-use-bash-guard.py" "$@"
