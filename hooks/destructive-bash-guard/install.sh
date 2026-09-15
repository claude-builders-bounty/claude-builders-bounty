#!/bin/bash
# One-command installer for Claude Code destructive bash guard hook
set -e

HOOKS_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOKS_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/guard.py" "$HOOKS_DIR/guard.py"
chmod +x "$HOOKS_DIR/guard.py"

echo "✅ Claude Code Destructive Bash Guard installed to $HOOKS_DIR/guard.py"
