#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_RULES = [
    (
        "recursive force delete",
        re.compile(r"(^|[\s;&|()])rm\s+-(?=[A-Za-z-]*r)(?=[A-Za-z-]*f)[A-Za-z-]*\b", re.I),
        "Refusing to run recursive force deletion. Review the target path and delete manually if intentional.",
    ),
    (
        "drop table",
        re.compile(r"\bDROP\s+TABLE\b", re.I),
        "Refusing to run DROP TABLE from an automated tool call.",
    ),
    (
        "truncate",
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.I),
        "Refusing to run TRUNCATE from an automated tool call.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;&|]*?(?:--force(?:\b|=)|\s-f(?:\s|$))", re.I),
        "Refusing to run a force push from an automated tool call.",
    ),
]

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.I)
WHERE_RE = re.compile(r"\bWHERE\b", re.I)


def read_event() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def extract_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    command = event.get("command")
    return command if isinstance(command, str) else ""


def project_path(event: dict[str, Any]) -> str:
    cwd = event.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return cwd

    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "workdir", "working_directory"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value

    return os.getcwd()


def delete_without_where(command: str) -> bool:
    statements = re.split(r";|\n", command)
    for statement in statements:
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    for _name, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return reason

    if delete_without_where(command):
        return "Refusing to run DELETE FROM without a WHERE clause."

    return None


def append_block_log(command: str, project: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project,
        "reason": reason,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }))


def main() -> int:
    event = read_event()
    command = extract_command(event)

    if not command:
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    append_block_log(command, project_path(event), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

