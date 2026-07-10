#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code — blocks destructive bash commands.

Installs at ~/.claude/hooks/pre-tool-use-hook.py
Claude Code calls this hook before executing any bash command.
If the hook exits with code 2, the command is blocked.

Blocked patterns:
  - rm -rf
  - DROP TABLE
  - git push --force (or --force-with-lease)
  - TRUNCATE
  - DELETE FROM (without WHERE clause)

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Ensure log directory exists
HOOKS_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOKS_DIR / "blocked.log"
HOOKS_DIR.mkdir(parents=True, exist_ok=True)

# Patterns that should be blocked — case-insensitive
BLOCKED_PATTERNS = [
    {
        "pattern": re.compile(r"\brm\s+(-[a-z]*r[a-z]*f?|--recursive)\s+(-[a-z]*f[a-z]*)?\s*", re.IGNORECASE),
        "name": "rm -rf",
        "reason": "Recursive force delete can destroy entire directory trees",
    },
    {
        "pattern": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "name": "DROP TABLE",
        "reason": "Drops entire database tables — irreversible data loss",
    },
    {
        "pattern": re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[\w\"\[\]`]+\s*;?", re.IGNORECASE),
        "name": "TRUNCATE",
        "reason": "Truncates table — deletes all rows without transaction log",
    },
    {
        "pattern": re.compile(r"\bDELETE\s+FROM\s+[\w\"\[\]`]+(\s+AS\s+\w+)?\s*;", re.IGNORECASE),
        "name": "DELETE FROM without WHERE",
        "reason": "DELETE FROM without WHERE clause deletes all rows",
    },
    {
        "pattern": re.compile(r"\bgit\s+push\s+(--force|-f)\b", re.IGNORECASE),
        "name": "git push --force",
        "reason": "Force push overwrites remote history — can destroy others' work",
    },
    {
        "pattern": re.compile(r"\bgit\s+push\s+--force-with-lease\b", re.IGNORECASE),
        "name": "git push --force-with-lease",
        "reason": "Force push variant — still rewrites remote history",
    },
    {
        "pattern": re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
        "name": "DROP DATABASE",
        "reason": "Drops entire database — catastrophic data loss",
    },
    {
        "pattern": re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;\s*:", re.IGNORECASE),
        "name": "fork bomb",
        "reason": "Fork bomb can crash the system",
    },
    {
        "pattern": re.compile(r"\bmkfs\.\w+\b", re.IGNORECASE),
        "name": "mkfs",
        "reason": "Formats filesystem — destroys all data on the device",
    },
    {
        "pattern": re.compile(r"\bdd\s+if=.*\s+of=/dev/", re.IGNORECASE),
        "name": "dd to device",
        "reason": "dd writing to /dev/ can overwrite disk devices",
    },
    {
        "pattern": re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
        "name": "redirect to device",
        "reason": "Writing directly to disk device files can destroy data",
    },
]


def log_block(command: str, pattern_name: str, reason: str):
    """Log a blocked command attempt."""
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] BLOCKED: {pattern_name} | Reason: {reason} | Command: {command[:200]}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def main():
    # Claude Code passes the tool input as JSON on stdin
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # If we can't parse the input, allow the command (fail open)
        sys.exit(0)

    # Extract the command from the tool input
    # Claude Code hook format: {"tool": "bash", "input": {"command": "..."}}
    command = ""
    if isinstance(input_data, dict):
        if "input" in input_data and isinstance(input_data["input"], dict):
            command = input_data["input"].get("command", "")
        elif "command" in input_data:
            command = input_data.get("command", "")
        elif "tool_input" in input_data:
            command = input_data["tool_input"].get("command", "")

    if not command:
        sys.exit(0)

    # Check against all blocked patterns
    for pattern_def in BLOCKED_PATTERNS:
        if pattern_def["pattern"].search(command):
            log_block(command, pattern_def["name"], pattern_def["reason"])
            # Exit code 2 blocks the command in Claude Code
            print(f"BLOCKED: Command matches dangerous pattern '{pattern_def['name']}'")
            print(f"Reason: {pattern_def['reason']}")
            print(f"Logged to {LOG_FILE}")
            sys.exit(2)

    # Command is safe — allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
