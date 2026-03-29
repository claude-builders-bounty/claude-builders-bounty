#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code — blocks destructive bash commands.

Reads JSON from stdin, checks .tool_input.command against dangerous patterns,
and outputs a deny JSON if matched. All blocked attempts are logged to
~/.claude/hooks/blocked.log in structured JSON format.

Zero external dependencies — uses only Python 3 stdlib.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


# --- Configuration ---

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*r", re.IGNORECASE),
        "Recursive force delete (rm -rf) is blocked — can cause irreversible data loss",
    ),
    (
        re.compile(r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f", re.IGNORECASE),
        "Recursive force delete (rm -rf) is blocked — can cause irreversible data loss",
    ),
    (
        re.compile(r"\brm\s+--recursive\s+--force\b", re.IGNORECASE),
        "Recursive force delete (rm --recursive --force) is blocked",
    ),
    (
        re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
        "SQL DROP statement is blocked — permanent schema destruction",
    ),
    (
        re.compile(r"\bgit\s+push\s+--force\b(?!-with-lease)", re.IGNORECASE),
        "Git force push is blocked — rewrites shared remote history",
    ),
    (
        re.compile(r"\bgit\s+push\s+-f\b", re.IGNORECASE),
        "Git force push (-f) is blocked — rewrites shared remote history",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(TABLE\s+)?", re.IGNORECASE),
        "SQL TRUNCATE is blocked — non-rollbackable row removal",
    ),
]

# DELETE FROM without WHERE — special case
RE_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
RE_WHERE_CLAUSE = re.compile(r"\bWHERE\b", re.IGNORECASE)

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def _deny(reason: str, command: str) -> None:
    """Output a deny decision and log the attempt."""
    # Log
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "BLOCKED",
        "command": command,
        "reason": reason,
        "cwd": os.getcwd(),
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Deny
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def check_command(command: str) -> None:
    """Check a command against all destructive patterns. Deny if matched."""
    if not command or not command.strip():
        return  # empty command — allow

    # Check fixed patterns
    for pattern, reason in PATTERNS:
        if pattern.search(command):
            _deny(reason + f". Command: {command}", command)

    # Special case: DELETE FROM without WHERE
    if RE_DELETE_FROM.search(command) and not RE_WHERE_CLAUSE.search(command):
        _deny(
            "SQL DELETE FROM without WHERE clause is blocked — would delete all rows. "
            f"Command: {command}",
            command,
        )

    # Safe — allow (exit silently)
    return


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return  # can't parse — allow

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    check_command(command)


if __name__ == "__main__":
    main()
