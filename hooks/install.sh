#!/usr/bin/env bash
# One-command installer for destructive_guard hook
# Usage: curl -sSL <raw-url> | bash
# Or:    bash install.sh

set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="destructive_guard.py"
HOOK_URL="https://raw.githubusercontent.com/Qwe1122333/claude-builders-bounty/main/hooks/destructive_guard.py"

mkdir -p "$HOOK_DIR"

# Download or copy the hook
if [ -f "./destructive_guard.py" ]; then
    cp "./destructive_guard.py" "$HOOK_DIR/destructive_guard.py"
else
    curl -sSL "$HOOK_URL" -o "$HOOK_DIR/destructive_guard.py"
fi

chmod +x "$HOOK_DIR/destructive_guard.py"

# Configure Claude Code settings
SETTINGS_FILE="$HOME/.claude/settings.json"
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
            "command": "python3 ~/.claude/hooks/destructive_guard.py"
          }
        ]
      }
    ]
  }
}
EOF
else
    # Merge hooks into existing settings using Python
    python3 -c "
import json, sys

with open('$SETTINGS_FILE') as f:
    settings = json.load(f)

hook_entry = {
    'matcher': 'Bash',
    'hooks': [
        {
            'type': 'command',
            'command': 'python3 ~/.claude/hooks/destructive_guard.py'
        }
    ]
}

hooks = settings.setdefault('hooks', {})
pre_tool = hooks.setdefault('PreToolUse', [])

# Check if already installed
for entry in pre_tool:
    if entry.get('matcher') == 'Bash':
        for h in entry.get('hooks', []):
            if 'destructive_guard' in h.get('command', ''):
                print('Hook already installed.')
                sys.exit(0)

pre_tool.append(hook_entry)

with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print('Hook installed successfully.')
"
fi

echo ""
echo "✅ destructive_guard hook installed!"
echo "   Hook:  $HOOK_DIR/destructive_guard.py"
echo "   Log:   $HOOK_DIR/blocked.log"
echo ""
echo "Test it: python3 $HOOK_DIR/destructive_guard.py --test"
