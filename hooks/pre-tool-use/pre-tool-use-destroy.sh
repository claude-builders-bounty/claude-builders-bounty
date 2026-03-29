#!/bin/bash
# Claude Code pre-tool-use hook: blocks destructive bash commands.
#
# Usage:
#   Place this file in ~/.claude/hooks/pre-tool-use-destroy.sh
#   Claude Code will automatically invoke it before every tool call.
#
#   Or run the setup script:
#     cp -r hooks/pre-tool-use ~/.claude/hooks/
#     chmod +x ~/.claude/hooks/pre-tool-use-destroy.sh
#
# What it blocks:
#   • rm -rf / (recursive root delete)
#   • DROP TABLE / DROP DATABASE / DROP SCHEMA
#   • git push --force / git push -f
#   • DELETE FROM without WHERE clause
#   • TRUNCATE
#   • Fork bombs, mkfs, dd to raw devices
#   • System shutdown/reboot commands
#
# All blocked attempts are logged to ~/.claude/hooks/blocked.log
#
# The hook reads Claude Code's JSON input from stdin and exits:
#   0 = allow the tool to run
#   1 = block the tool and show a message

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_HOOK="${SCRIPT_DIR}/destructive-hook.py"

# Fallback: if python3 not found, try python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    # Can't run the hook — fail open (don't block legitimate commands)
    echo "[destructive-hook] Warning: Python not found, allowing command" >&2
    exit 0
fi

PYTHON="${PYTHON3:-python}"

exec "$PYTHON" "$PYTHON_HOOK"
