#!/usr/bin/env bash
set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
HOOKS_DIR="${CLAUDE_DIR}/hooks"
SETTINGS_FILE="${CLAUDE_DIR}/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${HOOKS_DIR}"
cp "${SCRIPT_DIR}/bash-command-guard.py" "${HOOKS_DIR}/bash-command-guard.py"
chmod +x "${HOOKS_DIR}/bash-command-guard.py"

python3 -c "
import json
import os
from pathlib import Path

settings_file = Path('${SETTINGS_FILE}')
data = {}
if settings_file.exists():
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}

if 'hooks' not in data or not isinstance(data['hooks'], dict):
    data['hooks'] = {}

if 'PreToolUse' not in data['hooks'] or not isinstance(data['hooks']['PreToolUse'], list):
    data['hooks']['PreToolUse'] = []

hook_entry = {
    'matcher': 'Bash',
    'command': 'python3 ~/.claude/hooks/bash-command-guard.py'
}

exists = any(
    h.get('command') == hook_entry['command']
    for h in data['hooks']['PreToolUse']
    if isinstance(h, dict)
)

if not exists:
    data['hooks']['PreToolUse'].append(hook_entry)

with open(settings_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
"

echo "✅ bash-command-guard successfully installed in ~/.claude/hooks/ and registered in ~/.claude/settings.json"
