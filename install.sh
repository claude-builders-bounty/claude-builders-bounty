#!/usr/bin/env bash
set -euo pipefail

# Installation directory
HOOKS_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOKS_DIR"

# Copy safety interceptor and make executable
cp hooks/pre_tool_use_safety.py "$HOOKS_DIR/pre-tool-use"
chmod +x "$HOOKS_DIR/pre-tool-use"

echo "✅ Claude Code PreToolUse Safety Hook installed successfully to $HOOKS_DIR/pre-tool-use"
