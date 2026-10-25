#!/usr/bin/env bash
# Claude Code PreToolUse Hook Installer
# Install into ~/.claude/hooks/

set -e

HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/hooks/pre-tool-use/block_destructive_commands.py" "$HOOK_DIR/block_destructive_commands.py"
chmod +x "$HOOK_DIR/block_destructive_commands.py"

echo "✅ Claude Code destructive command hook successfully installed to $HOOK_DIR/block_destructive_commands.py"
echo "Blocked commands will be logged to $HOOK_DIR/blocked.log"
