#!/usr/bin/env python3
"""Claude Code pre-tool-use hook to block destructive bash commands.

Blocks:
- rm -rf
- git push --force / -f
- DROP TABLE
- TRUNCATE TABLE
- DELETE FROM without WHERE

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""
import sys
import re
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bgit\s+push\s+(?:--force|-f)\b',
    r'\bDROP\s+TABLE\b',
    r'\bTRUNCATE\s+TABLE\b',
    r'\bDELETE\s+FROM\b(?!\s+WHERE)',
]

LOG_PATH = Path.home() / '.claude' / 'hooks' / 'blocked.log'


def block_command(command):
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return f"Blocked destructive command: {command}"
    return None


def log_blocked(command, project):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] {command} | {project}\n")


def main():
    try:
        data = sys.stdin.read()
        command = data.strip()
        if not command:
            return 0
        project = str(Path.cwd())
        reason = block_command(command)
        if reason:
            log_blocked(command, project)
            print(f"BLOCKED: {reason}", file=sys.stderr)
            return 1
        return 0
    except Exception as e:
        print(f"Error in hook: {e}", file=sys.stderr)
        return 0


if __name__ == '__main__':
    sys.exit(main())