#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads a Claude Code hook event as JSON from stdin. When a dangerous Bash command
is detected, writes an audit record to ~/.claude/hooks/blocked.log and returns a
PreToolUse deny decision. Safe commands produce no output and exit successfully.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive forced deletion", re.compile(r"(?:^|[;&|]\s*)rm\s+(?=[^\n;&|]*\s)(?=[^\n;&|]*-[A-Za-z]*r)(?=[^\n;&|]*-[A-Za-z]*f)", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("forced git push", re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease|-if-includes)?|-f)(?:\s|$)", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)),
)

DELETE_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def destructive_reason(command: str) -> str | None:
    """Return the reason a command must be blocked, or None when it is safe."""
    for reason, pattern in PATTERNS:
        if pattern.search(command):
            return reason

    # Inspect each SQL statement separately so a WHERE in a different statement
    # cannot make a destructive DELETE appear safe.
    for statement in re.split(r";|\n", command):
        if DELETE_RE.search(statement) and not WHERE_RE.search(statement):
            return "DELETE FROM without WHERE"

    return None


def write_log(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    message = (
        f"Blocked destructive Bash command ({reason}). "
        "Use a narrower, reversible command or ask the user to approve a safer alternative."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Do not break normal Claude Code operation on malformed/non-hook input.
        return 0

    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = destructive_reason(command)
    if reason is None:
        return 0

    project_path = str(event.get("cwd") or os.getcwd())
    try:
        write_log(command, project_path, reason)
    except OSError:
        # Blocking takes precedence over logging availability.
        pass

    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
