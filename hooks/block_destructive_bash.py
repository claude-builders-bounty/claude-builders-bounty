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


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

RULES = (
    (
        "recursive force removal",
        re.compile(r"\brm\s+(?=[^;\n]*-[^\s;\n]*r)(?=[^;\n]*-[^\s;\n]*f)", re.IGNORECASE),
    ),
    (
        "DROP TABLE statement",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    ),
    (
        "TRUNCATE statement",
        re.compile(r"\btruncate\b", re.IGNORECASE),
    ),
    (
        "forced git push",
        re.compile(r"\bgit\s+push\b(?=[^;\n]*(?:--force(?:-with-lease)?|\s-f(?:\s|$)))", re.IGNORECASE),
    ),
)


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def bash_command(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") not in (None, "Bash"):
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = payload.get("input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd")
        if isinstance(value, str) and value:
            return value

    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def delete_without_where(command: str) -> bool:
    for statement in re.split(r";+", command):
        normalized = " ".join(statement.split()).lower()
        if re.search(r"\bdelete\s+from\b", normalized) and not re.search(r"\bwhere\b", normalized):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    for reason, pattern in RULES:
        if pattern.search(command):
            return reason
    if delete_without_where(command):
        return "DELETE FROM statement without WHERE clause"
    return None


def append_log(command: str, path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "project_path": path,
            "reason": reason,
            "command": command,
        },
        ensure_ascii=False,
    )
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def allow() -> None:
    print(json.dumps({"permissionDecision": "allow"}))


def deny(reason: str) -> None:
    message = (
        "Blocked destructive Bash command: "
        f"{reason}. Review the command manually before running it."
    )
    print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": message}))


def main() -> int:
    payload = read_payload()
    command = bash_command(payload)
    if not command:
        allow()
        return 0

    reason = blocked_reason(command)
    if reason is None:
        allow()
        return 0

    append_log(command, project_path(payload), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
