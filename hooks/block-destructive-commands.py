#!/usr/bin/env python3
"""
block-destructive-commands — Claude Code PreToolUse hook
Blocks destructive bash commands and logs attempts.
Install: cp block-destructive_commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive_commands.py
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "blocked.log")

PATTERNS = [
    (re.compile(r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-rf\s+|-fr\s+)', re.IGNORECASE),
     "rm -rf detected: recursive forced deletion is destructive and irreversible"),
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
     "DROP TABLE detected: destructive SQL operation that destroys table structure and data"),
    (re.compile(r'\bgit\s+push\b.*(--force|--force-with-lease|-f\s)', re.IGNORECASE),
     "git push --force detected: force pushing rewrites remote history and can destroy others' work"),
    (re.compile(r'\bTRUNCATE\s+(TABLE\s+)?\w+', re.IGNORECASE),
     "TRUNCATE detected: destructive SQL operation that permanently removes all rows"),
]

DELETE_NO_WHERE = re.compile(r'\bDELETE\s+FROM\s+\w+(\s*;?\s*$)', re.IGNORECASE)
HAS_WHERE = re.compile(r'\bWHERE\b', re.IGNORECASE)


def block_and_log(reason, command, cwd):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = f"[{timestamp}] BLOCKED | cwd={cwd} | reason={reason} | command={command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    print(f"BLOCKED: {reason}", file=sys.stderr)
    print(f"Attempted command: {command}", file=sys.stderr)
    print(f"Project path: {cwd}", file=sys.stderr)
    print(f"Logged to: {LOG_FILE}", file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd", "unknown")

    for pattern, reason in PATTERNS:
        if pattern.search(command):
            block_and_log(reason, command, cwd)

    if DELETE_NO_WHERE.search(command) and not HAS_WHERE.search(command):
        block_and_log(
            "DELETE FROM without WHERE detected: would delete ALL rows from the table",
            command, cwd
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
