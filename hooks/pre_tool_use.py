#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Blocks dangerous bash commands before execution.

Install: Copy to ~/.claude/hooks/pre_tool_use.py
Make executable: chmod +x ~/.claude/hooks/pre_tool_use.py
"""

import json
import sys
import os
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r'\brm\s+(-[rRf]+\s+|--recursive)', "rm with recursive/force flags"),
    (r'\brm\s+-[a-zA-Z]*r', "rm with recursive flag"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE statement"),
    (r'\bgit\s+push\s+.*--force\b', "Force push"),
    (r'\bgit\s+push\s+.*-f\b', "Force push (short flag)"),
    (r'\bTRUNCATE\b', "TRUNCATE statement"),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "DELETE without WHERE clause"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command: str, reason: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = ""
    command = ""

    if isinstance(data.get("tool"), dict):
        tool_name = data["tool"].get("name", "")
        inp = data["tool"].get("input", {})
        if isinstance(inp, dict):
            command = inp.get("command", "")

    if tool_name != "bash":
        sys.exit(0)

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason)
            print(f"BLOCKED: {reason}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
