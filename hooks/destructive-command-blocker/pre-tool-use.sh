#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Destructive Bash Command Blocker
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Invoke python or node engine depending on availability
if command -v python3 >/dev/null 2>&1; then
    exec python3 "${SCRIPT_DIR}/pre-tool-use.py"
elif command -v node >/dev/null 2>&1; then
    exec node "${SCRIPT_DIR}/pre_tool_use.js"
else
    # Fallback to pure bash regex matching
    INPUT=$(cat)
    if echo "$INPUT" | grep -Ei 'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f|DROP[[:space:]]+TABLE|git[[:space:]]+push.*--force|TRUNCATE[[:space:]]+TABLE' >/dev/null; then
        echo "⛔ COMMAND BLOCKED BY SECURITY HOOK: Destructive command detected." >&2
        exit 1
    fi
    exit 0
fi
