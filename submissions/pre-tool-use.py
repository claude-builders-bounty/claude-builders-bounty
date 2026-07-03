#!/usr/bin/env python3
"""pre-tool-use hook for Claude Code — blocks destructive bash commands.

Install: cp pre-tool-use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
"""
import os
import sys
import re
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', 'Destructive deletion (rm -rf)'),
    (r'\bDROP\s+TABLE\b', 'Database destruction (DROP TABLE)'),
    (r'\bgit\s+push\s+--force\b', 'Force push (git push --force)'),
    (r'\bTRUNCATE\b', 'Database truncation'),
    (r'\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE)', 'DELETE FROM without WHERE clause'),
    (r'\bDROP\s+DATABASE\b', 'Database destruction (DROP DATABASE)'),
    (r'\bformat\s+(C:|D:)\b', 'Drive format command'),
    (r':(){ :\|:& };:', 'Fork bomb'),
    (r'\bchmod\s+-R\s+777\s+/\b', 'Recursive world-writable root'),
]

HOOK_DIR = Path.home() / '.claude' / 'hooks'
LOG_FILE = HOOK_DIR / 'blocked.log'


def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked pattern. Returns (blocked, reason)."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ''


def log_blocked(command: str, reason: str) -> None:
    """Log blocked attempt to blocked.log."""
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    project = os.getcwd()
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{timestamp}] BLOCKED: {reason}\n')
        f.write(f'  Command: {command[:200]}\n')
        f.write(f'  Project: {project}\n\n')


def main():
    # Read the command from stdin (Claude Code hook protocol)
    command = sys.stdin.read().strip()
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, reason)
        print(
            f'🚫 BLOCKED: {reason}\n'
            f'   This command was intercepted by the pre-tool-use safety hook.\n'
            f'   If you need to run this, use .claude/hooks/bypass or run it manually.\n'
            f'   Attempt logged to ~/.claude/hooks/blocked.log',
            file=sys.stderr,
        )
        sys.exit(1)

    # Command is safe — pass through
    print(command)


if __name__ == '__main__':
    main()
