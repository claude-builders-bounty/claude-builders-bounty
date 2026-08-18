#!/usr/bin/env bash
#
# install.sh — Install the block-destructive hook for Claude Code
#
# Usage:
#   curl -sL <raw-url>/install.sh | bash
#   OR
#   git clone ... && cd hooks/block-destructive && bash install.sh
#
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/block_destructive.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "Installing block-destructive hook..."

# 1. Copy hook script
mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/block_destructive.py" "$HOOK_FILE"
chmod +x "$HOOK_FILE"

# 2. Register hook in settings.json
if [ ! -f "$SETTINGS_FILE" ]; then
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
EOF
    echo "✅ Created $SETTINGS_FILE with hook configuration."
else
    # Check if hook is already registered
    if grep -q "block_destructive" "$SETTINGS_FILE" 2>/dev/null; then
        echo "⚠️  Hook already registered in $SETTINGS_FILE"
    else
        echo ""
        echo "⚠️  $SETTINGS_FILE already exists."
        echo "   Add this to your hooks.PreToolUse array manually:"
        echo ""
        echo '  {'
        echo '    "matcher": "Bash",'
        echo '    "hooks": ['
        echo '      {'
        echo '        "type": "command",'
        echo '        "command": "~/.claude/hooks/block_destructive.py"'
        echo '      }'
        echo '    ]'
        echo '  }'
        echo ""
    fi
fi

echo "✅ Hook installed at $HOOK_FILE"
echo "✅ Blocked commands will be logged to $HOOK_DIR/blocked.log"
echo ""
echo "Done! The hook is now active for all Claude Code sessions."
