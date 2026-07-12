#!/bin/bash
set -e

HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/pre-tool-use"

mkdir -p "$HOOK_DIR"

cp pre-tool-use "$HOOK_FILE"
chmod +x "$HOOK_FILE"

echo "✅ Hook installed to $HOOK_FILE"
echo "   Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE"
echo "   Logs to: ~/.claude/hooks/blocked.log"
echo ""
echo "To test: run a destructive command in Claude Code and check the log."