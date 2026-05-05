#!/usr/bin/env bash
# Install the destructive command guard hook for Claude Code
set -e

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/block_destructive.py" "$HOOK_DIR/block_destructive.py"
chmod +x "$HOOK_DIR/block_destructive.py"

# Merge hook config into existing settings.json or create it
if [ -f "$SETTINGS_FILE" ]; then
    python3 -c "
import json, sys

settings_path = '$SETTINGS_FILE'
with open(settings_path) as f:
    settings = json.load(f)

hook_entry = {
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/block_destructive.py'}]
}

hooks = settings.setdefault('hooks', {})
pre_tool_use = hooks.setdefault('pre-tool-use', [])

# Avoid duplicates
for existing in pre_tool_use:
    if existing.get('matcher') == 'Bash':
        for h in existing.get('hooks', []):
            if 'block_destructive' in h.get('command', ''):
                print('Hook already configured.')
                sys.exit(0)

pre_tool_use.append(hook_entry)

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2)

print('Hook added to existing settings.json')
"
else
    cp "$(dirname "$0")/settings.json" "$SETTINGS_FILE"
    echo "Created settings.json with hook configuration"
fi

echo "Destructive command guard installed successfully."
