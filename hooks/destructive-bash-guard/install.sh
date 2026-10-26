#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.claude/hooks/destructive-bash-guard.py"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOME/.claude/hooks"
install -m 0755 "$SCRIPT_DIR/pre-tool-use.py" "$TARGET"

SETTINGS_TMP="$SETTINGS.tmp"
/usr/bin/python3 "$SCRIPT_DIR/install-settings.py" "$TARGET" "$SETTINGS" > "$SETTINGS_TMP"
mv "$SETTINGS_TMP" "$SETTINGS"

echo "Installed Claude Code hook: $TARGET"
