#!/bin/bash
# Install block-dangerous-bash hook for Claude Code
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"

echo "Installing block-dangerous-bash hook..."

# 1. Copy hook script
mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/block-dangerous-bash.sh" "${HOOK_DIR}/block-dangerous-bash.sh"
chmod +x "${HOOK_DIR}/block-dangerous-bash.sh"
echo "  Copied hook to ${HOOK_DIR}/block-dangerous-bash.sh"

# 2. Create or update ~/.claude/settings.json
if [ ! -f "$SETTINGS_FILE" ]; then
  cat > "$SETTINGS_FILE" <<'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-bash.sh"
          }
        ]
      }
    ]
  }
}
EOF
  echo "  Created ${SETTINGS_FILE}"
else
  echo ""
  echo "  NOTE: ${SETTINGS_FILE} already exists."
  echo "  Add the following to your PreToolUse hooks manually:"
  echo ""
  cat <<'EOF'
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "~/.claude/hooks/block-dangerous-bash.sh"
      }
    ]
  }
EOF
fi

echo ""
echo "Done. Blocked commands will be logged to: ${HOME}/.claude/hooks/blocked.log"
