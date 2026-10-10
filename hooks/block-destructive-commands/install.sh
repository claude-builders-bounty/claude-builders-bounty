#!/usr/bin/env bash
set -e

# Destination directory for Claude Code hooks
HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR"

# Copy pre-tool-use hook script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/pre-tool-use.py" "$HOOK_DIR/pre-tool-use.py"
chmod +x "$HOOK_DIR/pre-tool-use.py"

echo "✅ [SUCCESS] Destructive command protection hook installed to $HOOK_DIR/pre-tool-use.py"
echo "🛡️ Dangerous commands (rm -rf, DROP TABLE, git push --force, etc.) will now be safely blocked."
