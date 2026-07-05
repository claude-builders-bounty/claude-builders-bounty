#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from typing import Any


LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "recursive forced removal",
        re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b|\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b", re.I),
    ),
    ("DROP TABLE statement", re.compile(r"\bdrop\s+table\b", re.I)),
    ("TRUNCATE statement", re.compile(r"\btruncate\b", re.I)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$)", re.I)),
)


def _delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.I):
        remainder = command[match.start() :]
        statement = re.split(r";|\n|\|\||&&", remainder, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.I):
            return True
    return False


def detect_dangerous_command(command: str) -> str | None:
    for reason, pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return reason

    if _delete_without_where(command):
        return "DELETE FROM statement without a WHERE clause"

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str, command: str) -> None:
    message = (
        f"Blocked destructive Bash command: {reason}. "
        "Revise the request or ask the user for an explicit, safer alternative."
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
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = detect_dangerous_command(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or "")
    try:
        log_blocked_attempt(command, project_path, reason)
    except OSError as error:
        print(f"Failed to write blocked command log: {error}", file=sys.stderr)
    deny(reason, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
