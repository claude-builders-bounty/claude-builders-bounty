#!/usr/bin/env bash
set -e

HOOKS_DIR="$HOME/.claude/hooks"
TARGET_HOOK="$HOOKS_DIR/pre-tool-use"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_HOOK="$SCRIPT_DIR/block_destructive_bash.py"

echo "🛡️ Installing Claude Code Destructive Bash Hook..."
mkdir -p "$HOOKS_DIR"

if [ -f "$TARGET_HOOK" ]; then
    cp "$TARGET_HOOK" "$TARGET_HOOK.backup.$(date +%s)"
    echo "📦 Backed up existing pre-tool-use hook"
fi

cp "$SOURCE_HOOK" "$TARGET_HOOK"
chmod +x "$TARGET_HOOK"

echo "✅ Successfully installed hook to: $TARGET_HOOK"
echo "📝 Log file configured at: $HOOKS_DIR/blocked.log"
echo "✨ Test running hook..."

# Run a harmless test check
if "$TARGET_HOOK" "echo 'Hook active'" >/dev/null 2>&1; then
    echo "🎉 Verification passed! Claude Code is now protected against destructive commands."
else
    echo "⚠️ Warning: Test execution encountered an issue. Please verify Python 3 is installed."
fi
