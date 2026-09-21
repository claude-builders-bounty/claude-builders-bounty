#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RF_RE = re.compile(r"(?<![\w-])rm\s+(?:[^\n;&|]*\s)?-(?:[A-Za-z]*r[A-Za-z]*f|[A-Za-z]*f[A-Za-z]*r)\b", re.I)
DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.I)
TRUNCATE_RE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.I)
GIT_PUSH_FORCE_RE = re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease|-if-includes)?\b|(?:^|\s)-f(?:\s|$))", re.I)


def _delete_without_where(command: str) -> bool:
    """Return True if any DELETE FROM statement lacks a WHERE clause."""
    for match in re.finditer(r"\bDELETE\s+FROM\b", command, re.I):
        tail = command[match.start():]
        end = len(tail)
        for separator in (";", "\n", "&&", "||"):
            idx = tail.find(separator)
            if idx != -1:
                end = min(end, idx)
        statement = tail[:end]
        if not re.search(r"\bWHERE\b", statement, re.I):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks = (
        (RM_RF_RE, "recursive forced deletion (rm -rf)"),
        (DROP_TABLE_RE, "DROP TABLE"),
        (GIT_PUSH_FORCE_RE, "forced git push"),
        (TRUNCATE_RE, "TRUNCATE"),
    )
    for pattern, reason in checks:
        if pattern.search(command):
            return reason
    if _delete_without_where(command):
        return "DELETE FROM without a WHERE clause"
    return None


def log_block(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> dict[str, Any]:
    message = (
        f"Blocked destructive Bash command: {reason}. "
        "Use a safer, scoped alternative or ask the user for an explicit manual action."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
        "systemMessage": message,
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    cwd = str(event.get("cwd") or os.getcwd())
    log_block(command, cwd, reason)
    print(json.dumps(deny(reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
