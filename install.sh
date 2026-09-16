#!/usr/bin/env bash
# 1-step installer for Claude Code pre-tool-use hook
set -e

DEST="$HOME/.claude/hooks"
mkdir -p "$DEST"
cp hooks/block_destructive.py "$DEST/block_destructive.py"
cp hooks/block_destructive.sh "$DEST/block_destructive.sh"
chmod +x "$DEST/block_destructive.py" "$DEST/block_destructive.sh" 2>/dev/null || true

echo "✅ Claude Code pre-tool-use hook successfully installed!"
echo "📁 Location: $DEST"
echo "📜 Log File: $DEST/blocked.log"
