#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# install.sh — Install the block-destructive-commands hook for Claude Code
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/block_destructive.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "🔧 Installing block-destructive-commands hook..."

# 1. Ensure hooks directory exists
mkdir -p "$HOOK_DIR"

# 2. Make hook script executable
chmod +x "$HOOK_SCRIPT"

# 3. Add hook to Claude Code settings
if [ -f "$SETTINGS_FILE" ]; then
    # Settings file exists — check if hook is already configured
    if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
hooks = settings.get('hooks', {}).get('pre-tool-use', [])
for h in hooks:
    if 'block_destructive' in h.get('command', ''):
        sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        echo "✅ Hook is already configured in settings.json"
    else
        # Add the hook to existing settings
        python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
settings.setdefault('hooks', {}).setdefault('pre-tool-use', []).append({
    'type': 'command',
    'command': 'python3 $HOOK_SCRIPT',
    'timeout': 5000
})
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
print('✅ Hook added to existing settings.json')
"
    fi
else
    # Create new settings file with the hook
    python3 -c "
import json
settings = {
    'hooks': {
        'pre-tool-use': [{
            'type': 'command',
            'command': 'python3 $HOOK_SCRIPT',
            'timeout': 5000
        }]
    }
}
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
print('✅ Created settings.json with hook configured')
"
fi

echo ""
echo "🛡️  Hook installed successfully!"
echo "   Script: $HOOK_SCRIPT"
echo "   Config: $SETTINGS_FILE"
echo "   Log:    $HOOK_DIR/blocked.log"
echo ""
echo "The hook will now block dangerous commands like:"
echo "   • rm -rf"
echo "   • DROP TABLE / DROP DATABASE"
echo "   • git push --force"
echo "   • TRUNCATE"
echo "   • DELETE FROM without WHERE"
echo ""
echo "All blocked attempts are logged to $HOOK_DIR/blocked.log"
