#!/usr/bin/env bash
# Pre-tool-use hook wrapper for Claude Code.
# Forwards stdin to block-destructive.py and exits with its code.
# Place in ~/.claude/hooks/ and reference from settings.json:
#   { "hooks": { "PreToolUse": [{ "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/pre-tool-use.sh" }] }] } }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/block-destructive.py"
