#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks destructive bash commands."""

import sys
import json
import re
import os
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    # Dangerous file operations
    (r'\brm\s+-rf\b', 'rm -rf'),
    (r'\brm\s+-r\s+/', 'rm -r /'),
    (r'\brm\s+-rf\s+/', 'rm -rf /'),
    (r'\brm\s+-rf\s+~', 'rm -rf ~'),

    # Destructive database operations
    (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE'),
    (r'\bTRUNCATE\b', 'TRUNCATE'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM (no WHERE)'),

    # Dangerous git operations
    (r'\bgit\s+push\s+--force\b', 'git push --force'),
    (r'\bgit\s+push\s+-f\b', 'git push -f'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard'),

    # System-level dangerous operations
    (r'\bchmod\s+-R\s+777\b', 'chmod -R 777'),
    (r'\bchown\s+-R\b', 'chown -R'),
    (r'\bdd\s+if=', 'dd (disk destroyer)'),
    (r'\bmkfs\.', 'mkfs (format)'),
    (r'>\s*/dev/sd[a-z]', 'write to raw disk'),

    # Fork bomb
    (r':\(\)\s*\{', 'fork bomb pattern'),
]

BLOCK_LOG = os.path.expanduser('~/.claude/hooks/blocked.log')


def ensure_log_dir():
    os.makedirs(os.path.dirname(BLOCK_LOG), exist_ok=True)


def log_block(command, project_path=''):
    ensure_log_dir()
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'command': command,
        'project': project_path or os.getcwd()
    }
    with open(BLOCK_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def check_command(command):
    for pattern, name in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return name
    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')

    # Only intercept bash commands
    if tool_name != 'Bash':
        print(json.dumps(input_data))
        return

    blocked = check_command(command)
    if blocked:
        log_block(command, os.getcwd())

        msg = (
            f'BLOCKED: Detected potentially destructive command pattern "{blocked}"\n'
            f'Command: {command}\n'
            f'Reason: This command could cause irreversible data loss or system damage.\n'
            f'Blocked at: {datetime.now(timezone.utc).isoformat()}\n'
            f'Log: {BLOCK_LOG}'
        )
        result = {
            'decision': 'block',
            'reason': msg
        }
    else:
        result = {'decision': 'allow'}

    print(json.dumps(result))


if __name__ == '__main__':
    main()
