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


CHECKS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf removes files recursively and forcefully",
        re.compile(r"(?is)(?:^|[;&|]\s*|\bsudo\s+)rm\s+-(?=[A-Za-z]*r)(?=[A-Za-z]*f)[A-Za-z]*\b"),
    ),
    (
        "DROP TABLE can delete database schema",
        re.compile(r"(?is)\bdrop\s+table\b"),
    ),
    (
        "TRUNCATE can delete all rows from a table",
        re.compile(r"(?is)\btruncate(?:\s+table)?\b"),
    ),
    (
        "force pushing can overwrite remote history",
        re.compile(r"(?is)\bgit\s+push\b(?:(?![;&|]).)*(?:--force(?:-with-lease)?\b|(?:^|\s)-f(?:\s|$))"),
    ),
)


def delete_from_without_where(command: str) -> bool:
    """Return True when a DELETE FROM statement lacks a WHERE before its statement end."""
    for match in re.finditer(r"(?is)\bdelete\s+from\b", command):
        statement = command[match.start() :]
        statement = re.split(r"[;\n]", statement, maxsplit=1)[0]
        if not re.search(r"(?is)\bwhere\b", statement):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    for reason, pattern in CHECKS:
        if pattern.search(command):
            return reason
    if delete_from_without_where(command):
        return "DELETE FROM without WHERE can delete every matching row"
    return None


def project_path(payload: dict[str, Any]) -> str:
    return (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path(payload),
        "reason": reason,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_payload() -> dict[str, Any]:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def main() -> int:
    payload = read_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not command.strip():
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    log_block(payload, command, reason)
    print(
        "Blocked destructive Bash command: "
        f"{reason}. Rewrite the command to avoid irreversible changes, "
        "or ask the user for an explicit manual override.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
