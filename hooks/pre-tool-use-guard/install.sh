#!/usr/bin/env bash
#
# install.sh — Install the Pre-tool-use Destructive Command Guard
#
# Usage:
#   curl -sSL <raw-url>/install.sh | bash
#   — or —
#   git clone ... && cd hooks/pre-tool-use-guard && bash install.sh
#
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SCRIPT_NAME="guard.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

# Resolve the directory this script lives in
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FILE="$SCRIPT_DIR/$SCRIPT_NAME"

echo "🔧 Installing Claude Code pre-tool-use guard..."

# 1. Copy the hook script
mkdir -p "$HOOK_DIR"
cp "$SOURCE_FILE" "$HOOK_DIR/$SCRIPT_NAME"
chmod +x "$HOOK_DIR/$SCRIPT_NAME"
echo "   ✅ Copied $SCRIPT_NAME → $HOOK_DIR/"

# 2. Merge hook config into ~/.claude/settings.json
NEW_HOOK='{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "python3 ~/.claude/hooks/guard.py"
    }
  ]
}'

if [ ! -f "$SETTINGS_FILE" ]; then
    # No settings file yet — create one
    echo "{}" > "$SETTINGS_FILE"
fi

# Check if jq is available
if ! command -v jq &>/dev/null; then
    echo "   ⚠️  jq not found. Please install jq and re-run, or add the hook config manually."
    echo ""
    echo "   Add this to $SETTINGS_FILE under \"hooks.PreToolUse\":"
    echo "   $NEW_HOOK"
    exit 1
fi

# Read existing settings
EXISTING=$(cat "$SETTINGS_FILE")

# Check if PreToolUse hooks already exist
if echo "$EXISTING" | jq -e '.hooks.PreToolUse' &>/dev/null; then
    # Check if our hook is already installed
    if echo "$EXISTING" | jq -e '.hooks.PreToolUse[] | select(.hooks[]?.command == "python3 ~/.claude/hooks/guard.py")' &>/dev/null; then
        echo "   ℹ️  Hook already registered in settings.json — skipping"
    else
        # Append to existing PreToolUse array
        UPDATED=$(echo "$EXISTING" | jq --argjson hook "$NEW_HOOK" '.hooks.PreToolUse += [$hook]')
        echo "$UPDATED" > "$SETTINGS_FILE"
        echo "   ✅ Appended hook to existing PreToolUse config"
    fi
else
    # Create hooks.PreToolUse array
    UPDATED=$(echo "$EXISTING" | jq --argjson hook "$NEW_HOOK" '.hooks.PreToolUse = [$hook]')
    echo "$UPDATED" > "$SETTINGS_FILE"
    echo "   ✅ Added PreToolUse hook to settings.json"
fi

echo ""
echo "🎉 Installation complete!"
echo "   Hook script: $HOOK_DIR/$SCRIPT_NAME"
echo "   Settings:    $SETTINGS_FILE"
echo "   Block log:   $HOOK_DIR/blocked.log"
echo ""
echo "   The guard will automatically block destructive commands"
echo "   (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE)"
echo "   in all your Claude Code sessions."
