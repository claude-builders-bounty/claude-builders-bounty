#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code hook JSON from stdin. When the intercepted tool is
Bash, it inspects the attempted command and blocks high-risk destructive SQL,
Git, and filesystem patterns before execution.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-f[A-Za-z]*r|-r[A-Za-z]*f)\b", re.I),
        "Recursive forced removal is blocked because it can delete large parts of the project or filesystem.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.I),
        "DROP TABLE is blocked because it destroys database schema and data.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=)|\bgit\s+push\b[^\n;&|]*\s-f(?:\s|$)", re.I),
        "Force-pushing is blocked because it can rewrite shared history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate(?:\s+table)?\b", re.I),
        "TRUNCATE is blocked because it can delete all rows from a table.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\s+[\w.\"`\[\]-]+(?:(?!\bwhere\b)[^;\n])*($|;)", re.I),
        "DELETE FROM without a WHERE clause is blocked because it can delete every row in a table.",
    ),
]


def extract_command(payload: dict[str, Any]) -> str:
    """Extract the Bash command from common Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script")
        if isinstance(command, str):
            return command

    # Some wrappers flatten tool fields. Keep this fallback narrow.
    for key in ("command", "cmd", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    return tool_name.lower() in {"bash", "shell"} or bool(extract_command(payload))


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "root"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd")
        if isinstance(value, str) and value:
            return value

    return os.getcwd()


def find_block(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return name, reason
    return None


def log_block(command: str, path: str, rule: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rule": rule,
        "project_path": path,
        "attempted_command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If the hook cannot parse input, do not break normal commands.
        return 0

    if not isinstance(payload, dict) or not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    blocked = find_block(command)
    if not blocked:
        return 0

    rule, reason = blocked
    path = project_path(payload)
    log_block(command=command, path=path, rule=rule)

    print(
        "Blocked destructive Bash command.\n"
        f"Rule: {rule}\n"
        f"Reason: {reason}\n"
        f"Project: {path}\n"
        f"Log: {LOG_PATH}\n\n"
        "Choose a safer command, add a WHERE clause, remove force flags, or ask the user for explicit manual handling.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
