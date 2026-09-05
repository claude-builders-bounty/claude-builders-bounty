#!/usr/bin/env bash
set -e

HOOKS_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOKS_DIR"

cp hooks/pre_tool_use_bash_guard.py "$HOOKS_DIR/pre-tool-use.py"
cp hooks/pre-tool-use-bash-guard.sh "$HOOKS_DIR/pre-tool-use"
chmod +x "$HOOKS_DIR/pre-tool-use" "$HOOKS_DIR/pre-tool-use.py"

echo "Claude Code Pre-Tool-Use Destructive Command Guard successfully installed to $HOOKS_DIR"
