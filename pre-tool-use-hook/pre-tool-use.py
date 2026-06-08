#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands."""

import sys
import json
import re
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

DESTRUCTIVE_PATTERNS = [
    (r'rm\s+-rf\s', 'rm -rf (recursive force delete)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE (database destruction)'),
    (r'git\s+push\s+--force', 'git push --force (force push)'),
    (r'git\s+push\s+-f\b', 'git push -f (force push)'),
    (r'\bTRUNCATE\b', 'TRUNCATE (table truncation)'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM without WHERE clause'),
]

def is_destructive(command):
    for pattern, desc in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return desc
    return None

def log_block(command, reason, project_path):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'command': command,
        'reason': reason,
        'project': project_path
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if input_data.get('tool_name') != 'bash':
        sys.exit(0)

    command = input_data.get('tool_input', {}).get('command', '')
    project_path = input_data.get('cwd', '')

    reason = is_destructive(command)
    if reason:
        log_block(command, reason, project_path)
        result = {
            'decision': 'block',
            'reason': f'BLOCKED: {reason}\n'
                      f'Attempted command: {command}\n'
                      f'This command was blocked to prevent accidental destruction.\n'
                      f'If you need to run this command, please add // SAFE: <reason> as a comment.'
        }
        print(json.dumps(result))
        sys.exit(0)

    sys.exit(0)

if __name__ == '__main__':
    main()
