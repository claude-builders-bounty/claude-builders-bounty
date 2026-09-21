#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive bash commands.

Blocks:
- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without WHERE clause

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf command'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE SQL command'),
    (r'\bgit\s+push\s+--force(?!-with-lease)\b', 'git push --force command'),
    (r'\bTRUNCATE\s+(?:TABLE\s+)?\w+', 'TRUNCATE SQL command'),
    (r'\bDELETE\s+FROM\s+\w+\b(?!\s+WHERE)', 'DELETE FROM without WHERE clause'),
]

LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def check_command(command: str):
    """Check if command contains dangerous patterns."""
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, None

def log_blocked(command: str, description: str, project_path: str):
    """Log blocked attempt to log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | {project_path} | {description} | {command}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')
    cwd = input_data.get('cwd', os.getcwd())

    if tool_name != 'Bash' or not command:
        sys.exit(0)

    is_dangerous, description = check_command(command)
    if is_dangerous:
        log_blocked(command, description, cwd)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked dangerous command: {description}"
            }
        }
        print(json.dumps(output))
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()