#!/usr/bin/env bash
# install.sh — Deploy the destructive-bash-guard hook for Claude Code
#
# Usage:
#   bash install.sh
#
# This script:
#   1. Copies pre_tool_use.py to ~/.claude/hooks/
#   2. Registers the hook in ~/.claude/settings.json (merges, does not overwrite)

set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_SCRIPT="pre_tool_use.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

# --- Step 1: Deploy the hook script ---
mkdir -p "$HOOK_DIR"
cp "$HOOK_SCRIPT" "$HOOK_DIR/$HOOK_SCRIPT"
chmod +x "$HOOK_DIR/$HOOK_SCRIPT"
echo "✅ Hook script deployed to $HOOK_DIR/$HOOK_SCRIPT"

# --- Step 2: Register in settings.json ---
# Ensure settings.json exists
if [ ! -f "$SETTINGS_FILE" ]; then
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    echo '{}' > "$SETTINGS_FILE"
fi

# Use python to safely merge the hook config into settings.json
python3 -c "
import json, sys

settings_path = '$SETTINGS_FILE'
hook_command = '$HOOK_DIR/$HOOK_SCRIPT'

with open(settings_path, 'r') as f:
    settings = json.load(f)

# Ensure hooks structure exists
if 'hooks' not in settings:
    settings['hooks'] = {}

if 'PreToolUse' not in settings['hooks']:
    settings['hooks']['PreToolUse'] = []

# Check if our hook is already registered
existing = settings['hooks']['PreToolUse']
already_registered = any(
    h.get('hooks', [{}])[0].get('command', '').endswith('pre_tool_use.py')
    for h in existing
    if h.get('matcher') == 'Bash'
)

if already_registered:
    print('⚠️  Hook already registered in settings.json — skipping')
else:
    # Add our hook entry
    new_entry = {
        'matcher': 'Bash',
        'hooks': [
            {
                'type': 'command',
                'command': f'python3 {hook_command}',
                'timeout': 10
            }
        ]
    }
    settings['hooks']['PreToolUse'].append(new_entry)

    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

    print('✅ Hook registered in $SETTINGS_FILE')
"

echo ""
echo "🛡️  Destructive Bash Guard is now active!"
echo "   Blocked patterns: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE"
echo "   Blocked attempts logged to: $HOOK_DIR/blocked.log"
