#!/usr/bin/env bash
# claude-review.sh — wrapper for claude-review.py
# Ensures the correct Python interpreter is used and dependencies are checked.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/claude-review.py"

# ── Resolve Python ────────────────────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null && python --version 2>&1 | grep -q "Python 3"; then
    PYTHON=python
else
    echo "Error: Python 3 is required but not found." >&2
    exit 1
fi

# ── Check for ANTHROPIC_API_KEY ───────────────────────────────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "Error: ANTHROPIC_API_KEY is not set." >&2
    echo "  Export it first: export ANTHROPIC_API_KEY=sk-ant-..." >&2
    exit 1
fi

# ── Run ───────────────────────────────────────────────────────────────────────
exec "$PYTHON" "$PYTHON_SCRIPT" "$@"
