#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/hooks/block_destructive_bash.py" "$HOOK_DIR/block_destructive_bash.py"
chmod +x "$HOOK_DIR/block_destructive_bash.py"
echo "Installed Claude Code hook at $HOOK_DIR/block_destructive_bash.py"
echo "Add it as your PreToolUse hook command in Claude Code settings."
