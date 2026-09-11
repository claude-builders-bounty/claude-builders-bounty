#!/usr/bin/env bash
set -e

HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR"
cp "$(cd "$(dirname "$0")" && pwd)/guard.py" "$HOOK_DIR/pre-tool-use"
chmod +x "$HOOK_DIR/pre-tool-use"

echo "✅ Claude Code Destructive Bash Guard installed to $HOOK_DIR/pre-tool-use"
echo "Blocked commands will be logged to $HOOK_DIR/blocked.log"
