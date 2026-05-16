#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf'),
    (r'\bgit\s+push\s+(--force|-f)\b', 'git push --force'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
    (r'\bTRUNCATE\b', 'TRUNCATE'),
]

LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'


def is_delete_without_where(command: str) -> bool:
    if re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE):
        return not re.search(r'\bWHERE\b', command, re.IGNORECASE)
    return False


def check_command(command: str) -> str | None:
    for pattern, label in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return label
    if is_delete_without_where(command):
        return 'DELETE FROM without WHERE clause'
    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec='seconds')
    entry = f"[{ts}] BLOCKED: {reason}\n  command: {command!r}\n  project: {project_path}\n\n"
    with open(LOG_FILE, 'a') as f:
        f.write(entry)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get('tool_name') != 'Bash':
        sys.exit(0)

    command = data.get('tool_input', {}).get('command', '')
    project_path = os.getcwd()

    reason = check_command(command)
    if reason:
        log_blocked(command, project_path, reason)
        print(
            f"\n🚫 Blocked: '{reason}' detected in command.\n"
            f"   This operation was not executed. Check ~/.claude/hooks/blocked.log for details.\n",
            file=sys.stderr
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
