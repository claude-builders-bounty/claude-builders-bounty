#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code.
Blocks destructive bash commands before execution.
Install: place in ~/.claude/hooks/pre-tool-use
"""

import re, os, sys, json
from datetime import datetime

LOG_FILE = os.path.expanduser('~/.claude/hooks/blocked.log')

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+(-[rfR]+|--recursive|--force)', 'Recursive/force removal (rm -rf)'),
    (r'\bgit\s+push\s+.*--force\b', 'Force push (git push --force)'),
    (r'\bgit\s+push\s+.*-f\b', 'Force push (git push -f)'),
    (r'\bDROP\s+TABLE', 'DROP TABLE statement'),
    (r'\bDROP\s+DATABASE', 'DROP DATABASE statement'),
    (r'\bTRUNCATE\b', 'TRUNCATE statement'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM without WHERE clause'),
    (r'>\s*/dev/\w+', 'Write to /dev device'),
    (r':(){ :\|:& };:', 'Fork bomb'),
    (r'\bchmod\s+-R\s*0{3,4}\b', 'chmod -R to zero permissions'),
    (r'\bsudo\s+rm\b', 'sudo removal'),
    (r'\bmkfs\.', 'Format filesystem'),
]

def check_command(command: str):
    command_lower = command.lower()
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command_lower):
            return reason
    return None

def log_block(command, reason):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f'{datetime.utcnow().isoformat()} | {reason} | {os.getcwd()} | {command}\n')

def main():
    # Read the JSON input from stdin (Claude Code hooks format)
    # Input: { "command": "rm -rf /tmp/test" }
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    command = input_data.get('command', '')
    if not command:
        return

    reason = check_command(command)
    if reason:
        log_block(command, reason)
        print(json.dumps({
            "block": True,
            "message": f"⚠️  Blocked: {reason}\nLogged to ~/.claude/hooks/blocked.log",
        }))
    else:
        # Allow the command
        print('{"allow": true}')

if __name__ == '__main__':
    main()
