#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Blocks dangerous bash commands before execution.
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    (r'rm\s+(-[rf]*\s+)*(-rf|--recursive.*--force)\s', 'Dangerous recursive force delete (rm -rf)'),
    (r'rm\s+(-[rf]*\s+)*/(\s|$)', 'Attempt to delete root filesystem'),
    (r'rm\s+(-[rf]*\s+)*/\*', 'Attempt to delete all root files'),
    (r'DROP\s+TABLE', 'DROP TABLE detected without confirmation'),
    (r'git\s+push\s+.*--force', 'Force push detected'),
    (r'TRUNCATE', 'TRUNCATE statement detected'),
    (r'DELETE\s+FROM(?!.*WHERE)', 'DELETE without WHERE clause'),
    (r'DELETE\s+FROM\s+\w+\s*;', 'DELETE without WHERE clause'),
]

LOG_PATH = os.path.expanduser('~/.claude/hooks/blocked.log')

def log_attempt(command, reason, project_path):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason} | Command: {command} | Project: {project_path}\n"
    with open(LOG_PATH, 'a') as f:
        f.write(entry)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    project_path = input_data.get('cwd', os.getcwd())
    
    if tool_name != 'Bash':
        sys.exit(0)
    
    command = tool_input.get('command', '')
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_attempt(command, reason, project_path)
            print(f"⛔ BLOCKED: {reason}", file=sys.stderr)
            print(f"Command: {command}", file=sys.stderr)
            print(f"This command was blocked for safety. Check ~/.claude/hooks/blocked.log", file=sys.stderr)
            sys.exit(2)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
