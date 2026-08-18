#!/bin/bash
# 2-Command Installer for Claude Code Destructive Bash Command Safety Hook
HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR"
cp src/pre_tool_use_safety.py "$HOOK_DIR/pre_tool_use_safety.py"
chmod +x "$HOOK_DIR/pre_tool_use_safety.py"

echo "✅ Installed Claude Code safety hook to $HOOK_DIR/pre_tool_use_safety.py"
