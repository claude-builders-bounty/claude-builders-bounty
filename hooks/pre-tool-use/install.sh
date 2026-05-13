#!/bin/bash
set -e
HOOK_SRC="$(cd "$(dirname "$0")" && pwd)/destructive-guard.py"
HOOK_DST="$HOME/.claude/hooks/pre-tool-use"
mkdir -p "$HOOK_DST"
cp "$HOOK_SRC" "$HOOK_DST/destructive-guard.py"
chmod +x "$HOOK_DST/destructive-guard.py"
echo "✅ Installed destructive-guard hook to $HOOK_DST"
echo "   Restart Claude Code to activate."
