#!/usr/bin/env bash
set -e

# Target directory for Claude Code hooks
HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "Installing Claude Code Destructive Command Interceptor..."

# 1. Create directory and copy script
mkdir -p "$HOOKS_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/hooks/block_destructive.py" "$HOOKS_DIR/block_destructive.py"
cp "$SCRIPT_DIR/hooks/block-destructive.sh" "$HOOKS_DIR/block-destructive.sh"
chmod +x "$HOOKS_DIR/block_destructive.py" "$HOOKS_DIR/block-destructive.sh"

echo "✅ Hook installed to: $HOOKS_DIR/block_destructive.py"
echo "✅ Blocked logs will be written to: $HOOKS_DIR/blocked.log"

# 2. Configure ~/.claude/settings.json if it doesn't already have the hook
if [ -f "$SETTINGS_FILE" ]; then
  if grep -q "block_destructive.py" "$SETTINGS_FILE"; then
    echo "✅ Settings file ($SETTINGS_FILE) already configured."
    exit 0
  fi
fi

echo ""
echo "To activate globally in Claude Code, add this to $SETTINGS_FILE:"
cat << 'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
EOF
echo ""
echo "Installation complete!"
