#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin. When the pending tool call is Bash and the
command matches a dangerous pattern, appends a record to
~/.claude/hooks/blocked.log and returns a PreToolUse deny decision.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _sql_statements(command: str) -> Iterable[str]:
    """Yield rough SQL-ish statements from shell command text.

    This is intentionally conservative and dependency-free. It does not try to
    parse shell syntax; it only splits common SQL statement boundaries so a
    DELETE with a WHERE in the same statement is not blocked.
    """
    for statement in re.split(r";|\n", command):
        statement = statement.strip()
        if statement:
            yield statement


def blocked_reason(command: str) -> str | None:
    """Return the block reason for a dangerous command, or None if safe."""
    checks: list[tuple[str, str]] = [
        (
            r"(?i)(^|[;&|`$()\s])rm\s+-[^\n;&|]*r[^\n;&|]*f\b|(^|[;&|`$()\s])rm\s+-[^\n;&|]*f[^\n;&|]*r\b",
            "Blocked rm -rf style recursive force deletion.",
        ),
        (r"(?i)\bdrop\s+table\b", "Blocked DROP TABLE statement."),
        (r"(?i)\btruncate\b", "Blocked TRUNCATE statement."),
        (
            r"(?i)\bgit\s+push\b[^\n;&|]*?(--force\b|--force-with-lease\b|\s-f\b)",
            "Blocked forced git push.",
        ),
    ]

    for pattern, reason in checks:
        if re.search(pattern, command):
            return reason

    for statement in _sql_statements(command):
        if re.search(r"(?i)\bdelete\s+from\b", statement) and not re.search(
            r"(?i)\bwhere\b", statement
        ):
            return "Blocked DELETE FROM statement without a WHERE clause."

    return None


def log_block(command: str, cwd: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": cwd,
        "reason": reason,
        "attempted_command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str, command: str) -> None:
    message = f"{reason} Command was not run: {command}"
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
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive-command-guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    cwd = str(payload.get("cwd") or os.getcwd())
    log_block(command, cwd, reason)
    deny(reason, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
