#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands.

Reads JSON from stdin (Claude Code hook protocol), checks the command
against dangerous patterns, and either denies with explanation or
allows. Logs all blocked attempts to ~/.claude/hooks/blocked.log.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

PATTERNS = [
    (
        re.compile(r"\brm\s+.*(-r\b|--recursive|-rf\b|--rf\b|--force)", re.IGNORECASE),
        "Recursive file deletion can cause irreversible data loss",
    ),
    (
        re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)", re.IGNORECASE),
        "Dropping tables/databases destroys schema and data permanently",
    ),
    (
        re.compile(r"\bgit\s+push\s+.*(--force|-f\b|--force-with-lease)", re.IGNORECASE),
        "Force-pushing rewrites remote history and can destroy teammates' work",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(TABLE\s+)?", re.IGNORECASE),
        "TRUNCATE removes all rows from a table instantly with no rollback",
    ),
    (
        re.compile(r"\bDELETE\s+FROM\s+\S+", re.IGNORECASE),
        "DELETE FROM without WHERE clause removes all rows from the table",
    ),
    (
        re.compile(
            r"\bDELETE\s+FROM\s+\S+\s*;",
            re.IGNORECASE,
        ),
        "DELETE FROM without WHERE clause removes all rows from the table",
    ),
]

EXCLUDE_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def is_inside_quotes(command: str, start: int, end: int) -> bool:
    in_single = False
    in_double = False
    for i, ch in enumerate(command):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if start == i:
            return in_single or in_double
    return False


def log_blocked(timestamp: str, command: str, reason: str, cwd: str) -> None:
    entry = json.dumps({
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "cwd": cwd,
    })
    try:
        os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
        with open(BLOCKED_LOG, "a") as f:
            f.write(entry + "\n")
    except OSError:
        pass


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)

    data = json.loads(raw)
    command = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd", os.getcwd())

    if not command:
        sys.exit(0)

    for pattern, reason in PATTERNS:
        match = pattern.search(command)
        if not match:
            continue

        matched_text = match.group(0)
        if is_inside_quotes(command, match.start(), match.end()):
            continue

        if "DELETE" in matched_text.upper() and EXCLUDE_WHERE.search(command):
            continue

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_blocked(timestamp, command, reason, cwd)

        blocked_msg = match.group(0).strip()
        deny_reason = (
            f"Blocked: '{blocked_msg}' — {reason}. "
            f"If you are certain this is safe, run it manually in your terminal."
        )

        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": deny_reason,
            }
        }
        print(json.dumps(decision))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
