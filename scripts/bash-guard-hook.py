#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook — Bash Guard
Intercepts destructive bash commands before execution.
Blocks: rm -rf, DROP TABLE, TRUNCATE, git push --force, DELETE without WHERE.
"""

import json
import os
import re
import sys
from datetime import datetime

HOOK_DIR = os.path.expanduser('~/.claude/hooks')
LOG_FILE = os.path.join(HOOK_DIR, 'blocked.log')

DANGEROUS_PATTERNS = [
    (r'rm\s+-rf\s', 'rm -rf (recursive force delete)', 'Use `rm -r` with confirmation, or `trash` command instead'),
    (r'rm\s+-r\s+-f\s', 'rm -r -f (force recursive delete)', 'Same as above — remove individual files instead'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE (irreversible database operation)', 'Use a migration with a down instead. If needed, backup the table first'),
    (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE (removes all rows)', 'Use DELETE FROM with WHERE clause, or backup first'),
    (r'\bDELETE\s+FROM\s+(?!.*\bWHERE\b)', 'DELETE FROM without WHERE (deletes all rows)', 'Add a WHERE clause to scope the deletion'),
    (r'git\s+push\s+--force', 'git push --force (overwrites remote history)', 'Use `git push --force-with-lease` for safety'),
    (r'git\s+push\s+-f\b', 'git push -f (force push)', 'Use `git push --force-with-lease` instead'),
    (r':\(\)\s*\{', 'Fork bomb pattern detected', 'This pattern is typically malicious — rejected'),
    (r'>\s*/dev/sd[a-z]', 'Writing to raw block device', 'Do not write directly to block devices'),
    (r'\bchmod\s+777\b', 'chmod 777 (world-writable)', 'Use chmod 755 or more restrictive permissions'),
    (r'sudo\s+rm\s+-rf\s+/', 'sudo rm -rf / (system destruction)', 'NEVER run this — it destroys the system'),
    (r'\bFORMAT\b.*\bC:', 'Formatting Windows drive', 'Dangerous disk formatting — blocked'),
]


def log_blocked(command: str, cwd: str, reason: str):
    os.makedirs(HOOK_DIR, exist_ok=True)
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'command': command[:500],
        'cwd': cwd,
        'reason': reason,
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def check_command(command: str) -> str | None:
    """Check command against dangerous patterns. Returns block reason or None."""
    for pattern, label, suggestion in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return f'BLOCKED: {label}\n\nWhy: {suggestion}\n\nTo override this block, run:\n  export CLAUDE_ALLOW_DANGEROUS=1\n  # then re-run your command'
    return None


def main():
    # Read input from stdin (Claude Code passes stdin)
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # Only intercept bash/terminal commands
    if tool_name not in ('bash', 'terminal', 'execute_command'):
        sys.exit(0)

    command = tool_input.get('command', '') or tool_input.get('cmd', '') or ''
    if not command:
        sys.exit(0)

    cwd = os.getcwd()
    reason = check_command(command)

    if reason:
        log_blocked(command, cwd, reason)
        print(reason, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
