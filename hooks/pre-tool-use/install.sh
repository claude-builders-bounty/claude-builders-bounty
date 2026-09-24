#!/usr/bin/env bash
# Installs the pre-tool-use hook into ~/.claude/hooks/
set -e

HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR"
cp pre_tool_use_guard.py "$HOOK_DIR/pre_tool_use.py"
chmod +x "$HOOK_DIR/pre_tool_use.py"

echo "[✓] Hook installed to $HOOK_DIR/pre_tool_use.py"
