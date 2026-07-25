#!/usr/bin/env bash
# Install the pre-tool-use hook for Claude Code
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_SRC="$(cd "$(dirname "$0")" && pwd)/pre_tool_use.py"
HOOK_DST="$HOOK_DIR/pre_tool_use.py"

mkdir -p "$HOOK_DIR"

if [[ -f "$HOOK_DST" ]]; then
    echo "⚠️  Hook already exists at $HOOK_DST"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "❌ Installation cancelled."
        exit 1
    fi
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "✅ Installed pre-tool-use hook to $HOOK_DST"
echo ""
echo "📋 Blocked patterns:"
echo "   - rm -rf /, /*, ~ (filesystem destruction)"
echo "   - git push --force, reset --hard (git destruction)"
echo "   - DROP TABLE, DELETE/UPDATE without WHERE (database safety)"
echo "   - dd, mkfs, format (disk operations)"
echo "   - docker system prune -a (container destruction)"
echo ""
echo "📝 Blocked commands are logged to: $HOOK_DIR/blocked.log"
echo ""
echo "To test: run any blocked command and Claude Code will show a safety warning."
echo "To uninstall: rm $HOOK_DST"
