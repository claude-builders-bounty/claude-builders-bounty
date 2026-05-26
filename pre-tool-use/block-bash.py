#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Install: ln -sf "$(pwd)/pre-tool-use" ~/.claude/hooks/
"""

import json
import re
import sys
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    (re.compile(r'\brm\s+(-[rfR]+|--recursive\b|--force\b)', re.IGNORECASE), 'rm -rf / recursive delete'),
    (re.compile(r'\bDROP\s+TABLE', re.IGNORECASE), 'DROP TABLE (destructive SQL)'),
    (re.compile(r'\bgit\s+push\s+--force', re.IGNORECASE), 'git push --force (force push)'),
    (re.compile(r'\bTRUNCATE\b', re.IGNORECASE), 'TRUNCATE (destructive SQL)'),
    (re.compile(r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', re.IGNORECASE), 'DELETE FROM without WHERE clause'),
    (re.compile(r'\brm\s+-rf\s*[/~]', re.IGNORECASE), 'rm -rf on root/home directory'),
    (re.compile(r'>\s*/dev/\w+', re.IGNORECASE), 'Writing to /dev/ special files'),
    (re.compile(r'\bdd\s+if=.*\sof=', re.IGNORECASE), 'dd command overwriting device'),
    (re.compile(r'\bmkfs\.', re.IGNORECASE), 'Filesystem creation tool'),
]

def log_block(cmd, cwd, reason):
    """Log blocked command attempt."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] BLOCKED: {reason}\n")
            f.write(f"  Command: {cmd}\n")
            f.write(f"  Project: {cwd}\n")
            f.write(f"  { '-' * 60 }\n")
    except Exception:
        pass


def check_command(cmd, cwd):
    """Check a command against dangerous patterns. Returns (blocked, reason)."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(cmd):
            return True, reason
    return False, None


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse input, allow by default
        print(json.dumps({"is_blocked": False}))
        return

    tool_name = data.get("name", "")
    tool_input = data.get("input", {})

    # Only check bash tool calls
    if tool_name != "bash":
        print(json.dumps({"is_blocked": False}))
        return

    command = tool_input.get("command", "")
    cwd = tool_input.get("cwd", os.getcwd())

    if not command.strip():
        print(json.dumps({"is_blocked": False}))
        return

    blocked, reason = check_command(command, cwd)
    if blocked:
        log_block(command, cwd, reason)
        print(json.dumps({
            "is_blocked": True,
            "message": f"⛔ Blocked: {reason}\n\n"
                       f"This command was blocked by the pre-tool-use safety hook.\n"
                       f"If you need to run this command, manually execute it outside Claude Code."
        }))
    else:
        print(json.dumps({"is_blocked": False}))


if __name__ == "__main__":
    main()
