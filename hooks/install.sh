#!/bin/bash
# Install the pre-tool-use hook for Claude Code
# Usage: bash install.sh

HOOK_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOOK_DIR"

# Install the hook
cp "$SCRIPT_DIR/pre-tool-use-hook.py" "$HOOK_DIR/pre-tool-use"
chmod +x "$HOOK_DIR/pre-tool-use"

echo "✅ Installed pre-tool-use hook to $HOOK_DIR/pre-tool-use"
echo "📝 Blocked commands will be logged to $HOOK_DIR/blocked.log"
echo ""
echo "To test: claude code will now block dangerous commands automatically."
