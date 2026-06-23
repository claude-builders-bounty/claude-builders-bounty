#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
# This is a thin wrapper that delegates to the Python hook.
# Install: cp this file to ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/block-destructive.py"
