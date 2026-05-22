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


RM_RF_RE = re.compile(
    r"(?<![\w-])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|"
    r"(?:--recursive\s+--force|--force\s+--recursive))\b"
)
GIT_FORCE_PUSH_RE = re.compile(
    r"\bgit\s+push\b[^\n;&|]*\s(?:--force(?:-with-lease|-if-includes)?|-f)\b"
)
DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def load_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def statement_segments(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n", command) if part.strip()]


def destructive_reason(command: str) -> str | None:
    if RM_RF_RE.search(command):
        return "rm -rf style recursive forced deletion is blocked"

    if GIT_FORCE_PUSH_RE.search(command):
        return "git push force operation is blocked"

    if DROP_TABLE_RE.search(command):
        return "DROP TABLE is blocked"

    if TRUNCATE_RE.search(command):
        return "TRUNCATE is blocked"

    for segment in statement_segments(command):
        if DELETE_FROM_RE.search(segment) and not WHERE_RE.search(segment):
            return "DELETE FROM without a WHERE clause is blocked"

    return None


def append_block_log(command: str, project_path: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = load_payload()
    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = destructive_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    append_block_log(command, project_path, reason)
    print(
        "Blocked destructive Bash command: "
        f"{reason}. The attempted command was logged to ~/.claude/hooks/blocked.log.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
