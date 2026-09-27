#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell/SQL commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

RM_RF_RE = re.compile(r"(?i)(?:^|[;&|]\s*)rm\s+(?:-[A-Za-z]*[rf][A-Za-z]*\s+|(?:-r|-f|--recursive|--force)\s+)+(?:--\s+)?\S+")
DROP_TABLE_RE = re.compile(r"(?i)\bDROP\s+TABLE\b")
GIT_FORCE_RE = re.compile(r"(?i)(?:^|[;&|]\s*)git\s+push\b[^\n;]*?(?:--force(?:-with-lease)?\b|(?:^|\s)-f(?:\s|$))")
TRUNCATE_RE = re.compile(r"(?i)\bTRUNCATE(?:\s+TABLE)?\b")
DELETE_FROM_RE = re.compile(r"(?is)\bDELETE\s+FROM\b")


def _delete_without_where(command: str) -> bool:
    """Return True if any DELETE FROM statement lacks a WHERE clause."""
    for match in DELETE_FROM_RE.finditer(command):
        tail = command[match.start():]
        end = len(tail)
        for marker in (";", "\n"):
            pos = tail.find(marker)
            if pos != -1:
                end = min(end, pos)
        statement = tail[:end]
        if not re.search(r"(?i)\bWHERE\b", statement):
            return True
    return False


def block_reason(command: str) -> str | None:
    checks = (
        (RM_RF_RE, "rm -rf / recursive forced deletion"),
        (DROP_TABLE_RE, "DROP TABLE"),
        (GIT_FORCE_RE, "git push --force"),
        (TRUNCATE_RE, "TRUNCATE"),
    )
    for pattern, reason in checks:
        if pattern.search(command):
            return reason
    if _delete_without_where(command):
        return "DELETE FROM without WHERE"
    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    clean_command = command.replace("\r", "\\r").replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={clean_command}\n"
        )


def deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive command: {reason}",
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Malformed hook input should not break ordinary tool execution.
        return 0

    if payload.get("tool_name") not in {"Bash", "PowerShell"}:
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = block_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked(command, project_path, reason)
    json.dump(deny(reason), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
