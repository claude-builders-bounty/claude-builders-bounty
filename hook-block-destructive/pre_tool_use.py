#!/usr/bin/env python3
"""Pre-tool-use hook: blocks destructive bash commands for Claude Code.

Place at ~/.claude/hooks/pre_tool_use.py
"""

import json, os, re, sys
from datetime import datetime, timezone

BLOCK_PATTERNS = [
    (r'\brm\s+(-[rRf]+\s+)*[/~]', 'rm (force/recursive delete)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
    (r'\bgit\s+push\s+.*(--force|-f)', 'git push --force'),
    (r'\bTRUNCATE\s+(TABLE\s+)?', 'TRUNCATE TABLE'),
    (r'\bDELETE\s+FROM\b\s*(?!.*\bWHERE\b)', 'DELETE FROM without WHERE'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard'),
    (r'\bchmod\s+777\b', 'chmod 777 (world-writable)'),
    (r'>\s*/dev/sd[a-z]', 'raw disk write'),
    (r'\bmkfs\.', 'filesystem format (mkfs)'),
    (r':\(\)\s*\{', 'fork bomb pattern'),
]
LOG_PATH = os.path.expanduser('~/.claude/hooks/blocked.log')

def load_hook_input() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}

def extract_command(data: dict) -> str:
    tool_input = data.get('tool_input', {})
    if isinstance(tool_input, dict):
        return tool_input.get('command', '')
    return str(tool_input)

def is_blocked(command: str) -> tuple[bool, str]:
    for pattern, label in BLOCK_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, label
    return False, ''

def log_block(command: str, reason: str, project: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] BLOCKED | reason={reason} | project={project} | cmd={command}\n"
    with open(LOG_PATH, 'a') as f:
        f.write(entry)

def main():
    data = load_hook_input()
    command = extract_command(data)
    if not command:
        sys.exit(0)

    blocked, reason = is_blocked(command)
    if blocked:
        project = os.getcwd()
        log_block(command, reason, project)
        print(json.dumps({
            'decision': 'block',
            'reason': f'Destructive: {reason}',
            'message': f'Command blocked ({reason}). Override with CLAUDE_ALLOW_DESTRUCTIVE=1 or remove from deny list.',
            'allowOverride': True
        }))
        sys.exit(2)

    sys.exit(0)

if __name__ == '__main__':
    main()