#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "recursive force delete with rm",
        re.compile(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b"),
    ),
    ("DROP TABLE statement", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("TRUNCATE statement", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("forced git push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=)", re.IGNORECASE)),
]

DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def load_event() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        deny(f"Invalid hook JSON input: {exc}")
        raise SystemExit(0)


def find_block_reason(command: str) -> str | None:
    for reason, pattern in PATTERNS:
        if pattern.search(command):
            return reason

    delete_match = DELETE_FROM.search(command)
    if delete_match and not WHERE.search(command[delete_match.end() :]):
        return "DELETE FROM statement without a WHERE clause"

    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    log_path = Path(
        os.environ.get(
            "CLAUDE_HOOKS_BLOCKED_LOG",
            str(Path.home() / ".claude" / "hooks" / "blocked.log"),
        ),
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project = project_path.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp}\treason={reason}\tproject={safe_project}\tcommand={safe_command}\n",
        )


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked destructive Bash command: "
                        f"{reason}. Rewrite the command to be narrower, reversible, "
                        "or explicitly reviewed by a human."
                    ),
                },
            },
        ),
    )


def main() -> int:
    event = load_event()
    if event.get("hook_event_name") != "PreToolUse":
        return 0
    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = str(event.get("cwd") or os.getcwd())
    log_blocked(command, project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
