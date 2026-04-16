#!/usr/bin/env bash
# Install the destructive-command blocker hook for Claude Code.
# Usage: bash install.sh

set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$HOOKS_DIR"
cp "$SCRIPT_DIR/block-destructive.py" "$HOOKS_DIR/block-destructive.py"
chmod +x "$HOOKS_DIR/block-destructive.py"

# Register hook in Claude Code settings
SETTINGS="$HOME/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
    # Merge with existing settings using Python
    python3 -c "
import json
from pathlib import Path

settings_path = Path('$SETTINGS')
settings = json.loads(settings_path.read_text())

hooks = settings.get('hooks', {})
pre_tool = hooks.get('PreToolUse', [])
if not isinstance(pre_tool, list):
    pre_tool = [pre_tool]

# Avoid duplicates
hook_entry = {'command': '$HOOKS_DIR/block-destructive.py'}
if hook_entry not in pre_tool:
    pre_tool.append(hook_entry)

hooks['PreToolUse'] = pre_tool
settings['hooks'] = hooks
settings_path.write_text(json.dumps(settings, indent=2))
print('✅ Hook registered in settings.json')
"
else
    mkdir -p "$(dirname "$SETTINGS")"
    cat > "$SETTINGS" << 'EOF'
{
  "hooks": {
    "PreToolUse": [
      {"command": "~/.claude/hooks/block-destructive.py"}
    ]
  }
}
EOF
    echo "✅ Created settings.json with hook"
fi

echo "✅ Safety hook installed. It will block:"
echo "   - rm -rf / rm -fr"
echo "   - DROP TABLE"
echo "   - git push --force / -f"
echo "   - TRUNCATE"
echo "   - DELETE FROM (without WHERE)"
echo ""
echo "Blocked attempts are logged to: ~/.claude/hooks/blocked.log"
