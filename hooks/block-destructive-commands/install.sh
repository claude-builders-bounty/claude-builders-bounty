#!/usr/bin/env bash
# One-command installer for Claude Code PreToolUse Destructive Command Blocker
set -e

HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "==> Setting up Claude Code PreToolUse hook directory: $HOOKS_DIR"
mkdir -p "$HOOKS_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy hook script
cp "$SCRIPT_DIR/block_destructive_commands.py" "$HOOKS_DIR/block_destructive_commands.py"
chmod +x "$HOOKS_DIR/block_destructive_commands.py"

echo "==> Hook installed to $HOOKS_DIR/block_destructive_commands.py"
echo "==> Ensure your $SETTINGS_FILE includes the PreToolUse hook:"
echo ""
echo '  "hooks": {'
echo '    "PreToolUse": ['
echo '      {'
echo '        "matcher": "Bash",'
echo '        "hooks": ['
echo '          {'
echo '            "type": "command",'
echo '            "command": "python3 ~/.claude/hooks/block_destructive_commands.py"'
echo '          }'
echo '        ]'
echo '      }'
echo '    ]'
echo '  }'
echo ""
echo "==> Setup complete!"
