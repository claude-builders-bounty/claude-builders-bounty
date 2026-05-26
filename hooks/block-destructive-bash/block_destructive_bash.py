#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RM_RF_PATTERN = re.compile(
    r"(?<!\S)rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|(?:--recursive\s+--force|--force\s+--recursive))\b",
    re.IGNORECASE,
)
DROP_TABLE_PATTERN = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_PATTERN = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
GIT_FORCE_PUSH_PATTERN = re.compile(r"\bgit\s+push\b[^\n;&|]*(?:\s--force(?:-with-lease)?\b|\s-f\b)", re.IGNORECASE)
DELETE_FROM_PATTERN = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_PATTERN = re.compile(r"\bWHERE\b", re.IGNORECASE)


def load_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def sql_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n", command) if part.strip()]


def detect(command: str) -> str | None:
    checks = [
        (RM_RF_PATTERN, "rm -rf style recursive forced deletion"),
        (DROP_TABLE_PATTERN, "DROP TABLE statement"),
        (TRUNCATE_PATTERN, "TRUNCATE statement"),
        (GIT_FORCE_PUSH_PATTERN, "git force push"),
    ]
    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    for statement in sql_statements(command):
        if DELETE_FROM_PATTERN.search(statement) and not WHERE_PATTERN.search(statement):
            return "DELETE FROM statement without WHERE clause"

    return None


def append_log(command: str, cwd: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked destructive Bash command: {reason}.",
                }
            }
        )
    )


def main() -> int:
    payload = load_input()
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    reason = detect(command)
    if not reason:
        return 0

    cwd = str(payload.get("cwd") or os.getcwd())
    append_log(command, cwd, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
