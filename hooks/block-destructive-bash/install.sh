#!/usr/bin/env bash
# install.sh — one-command installer for the destructive-bash hook
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR=".claude/hooks"
TARGET_SETTINGS=".claude/settings.json"

mkdir -p "$TARGET_DIR"
cp "$SCRIPT_DIR/.claude/hooks/block-destructive-bash.py" "$TARGET_DIR/"
chmod +x "$TARGET_DIR/block-destructive-bash.py"

# Merge hook config into settings.json (create if missing)
if [ ! -f "$TARGET_SETTINGS" ]; then
    cat > "$TARGET_SETTINGS" <<'EOF'
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
EOF
else
    echo "⚠️  $TARGET_SETTINGS already exists. Merge the hook entry manually:"
    echo '  Add "pre-tool-use" hook: "python3 .claude/hooks/block-destructive-bash.py"'
fi

echo "✅ Hook installed. Claude Code will now block destructive bash commands."
echo "📝 Blocked attempts are logged to ~/.claude/hooks/blocked.log"
