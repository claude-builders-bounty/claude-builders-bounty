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


class BlockRule:
    def __init__(self, name: str, pattern: str, reason: str, flags: int = re.IGNORECASE):
        self.name = name
        self.pattern = re.compile(pattern, flags)
        self.reason = reason

    def matches(self, command: str) -> bool:
        return bool(self.pattern.search(command))


BLOCK_RULES = [
    BlockRule(
        "rm -rf",
        r"\brm\s+(?:-[^\s]*[rR][^\s]*[fF]|-[^\s]*[fF][^\s]*[rR])\b",
        "recursive forced deletion can irreversibly remove project or system files",
    ),
    BlockRule(
        "DROP TABLE",
        r"\bdrop\s+table\b",
        "DROP TABLE removes database tables and data",
    ),
    BlockRule(
        "TRUNCATE",
        r"\btruncate(?:\s+table)?\b",
        "TRUNCATE deletes all rows from a table",
    ),
    BlockRule(
        "git push --force",
        r"\bgit\s+push\b[^\n;&|]*(?:--force(?![-\w])|--force-with-lease(?![-\w])|(?:^|\s)-f(?:\s|$))",
        "force pushing can overwrite remote history",
    ),
]


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"command": raw}
    return payload if isinstance(payload, dict) else {}


def nested_get(mapping: dict[str, Any], *path: str) -> Any:
    value: Any = mapping
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def extract_tool_name(payload: dict[str, Any]) -> str:
    value = payload.get("tool_name") or payload.get("tool") or payload.get("name")
    return str(value or "")


def extract_command(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("command"),
        nested_get(payload, "tool_input", "command"),
        nested_get(payload, "input", "command"),
        nested_get(payload, "params", "command"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        nested_get(payload, "tool_input", "cwd"),
        nested_get(payload, "input", "cwd"),
        os.environ.get("PWD"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return os.getcwd()


def is_bash_tool(payload: dict[str, Any], command: str) -> bool:
    tool_name = extract_tool_name(payload).lower()
    if tool_name:
        return tool_name in {"bash", "shell", "exec_command"}
    return bool(command)


def has_where_after_delete_from(statement: str) -> bool:
    return bool(re.search(r"\bwhere\b", statement, re.IGNORECASE))


def blocked_reason(command: str) -> tuple[str, str] | None:
    if re.match(r"^\s*(?:echo|printf)\b", command):
        return None

    for statement in re.split(r"[;\n]", command):
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE):
            if not has_where_after_delete_from(statement):
                return (
                    "DELETE FROM without WHERE",
                    "DELETE FROM without a WHERE clause can erase an entire table",
                )

    for rule in BLOCK_RULES:
        if rule.matches(command):
            return rule.name, rule.reason
    return None


def log_blocked(command: str, project_path: str, pattern: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "pattern": pattern,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def main() -> int:
    payload = load_payload()
    command = extract_command(payload)

    if not command or not is_bash_tool(payload, command):
        return 0

    result = blocked_reason(command)
    if result is None:
        return 0

    pattern, reason = result
    project_path = extract_project_path(payload)
    log_blocked(command, project_path, pattern)

    message = (
        "Blocked dangerous Bash command.\n"
        f"Pattern: {pattern}\n"
        f"Reason: {reason}.\n"
        f"Project path: {project_path}\n"
        f"Log: {LOG_PATH}"
    )
    print(
        json.dumps(
            {
                "decision": "block",
                "permissionDecision": "deny",
                "reason": message,
                "command": command,
            }
        )
    )
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
