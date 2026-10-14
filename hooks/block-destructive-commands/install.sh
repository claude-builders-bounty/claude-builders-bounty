#!/usr/bin/env bash
# Installer script for Claude Code PreToolUse Destructive Command Guard
# Installs hook files to ~/.claude/hooks and configures ~/.claude/settings.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
HOOKS_DIR="${CLAUDE_DIR}/hooks"
SETTINGS_FILE="${CLAUDE_DIR}/settings.json"

echo "Installing Claude Code Destructive Command Guard..."

# 1. Create hooks directory
mkdir -p "$HOOKS_DIR"

# 2. Copy hook scripts and ensure executable permissions
cp "$SCRIPT_DIR/block_destructive.py" "$HOOKS_DIR/block_destructive.py"
cp "$SCRIPT_DIR/block_destructive.sh" "$HOOKS_DIR/block_destructive.sh"
chmod +x "$HOOKS_DIR/block_destructive.py" "$HOOKS_DIR/block_destructive.sh"

# 3. Configure ~/.claude/settings.json cleanly
python3 -c "
import json
from pathlib import Path

settings_path = Path('$SETTINGS_FILE')
settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8'))
    except Exception:
        settings = {}

hooks = settings.setdefault('hooks', {})
pre_tool_use = hooks.setdefault('PreToolUse', [])

hook_cmd = '$HOOKS_DIR/block_destructive.py'

# Check if hook is already registered
already_exists = any(
    h.get('matcher') == 'Bash' and
    any(hook_cmd in sub.get('command', '') for sub in h.get('hooks', []))
    for h in pre_tool_use
)

if not already_exists:
    pre_tool_use.append({
        'matcher': 'Bash',
        'hooks': [
            {
                'type': 'command',
                'command': hook_cmd
            }
        ]
    })
    settings_path.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    print('Configured PreToolUse hook in ~/.claude/settings.json')
else:
    print('PreToolUse hook is already configured in ~/.claude/settings.json')
"

echo "Installation complete! Blocked command logs will be recorded in ~/.claude/hooks/blocked.log."
