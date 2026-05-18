#!/usr/bin/env python3
"""PreToolUse hook that blocks dangerous Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


PATTERNS = [
    (
        "rm -rf",
        re.compile(r"\brm\s+-(?:[^\s-]*r[^\s-]*f|[^\s-]*f[^\s-]*r)\b", re.IGNORECASE),
        "Recursive force delete can permanently remove project or system files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE can permanently delete database schema and data.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE can permanently remove all rows from a table.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b(?=[^\n;|&]*\s(?:--force(?:-with-lease)?|-f)\b)", re.IGNORECASE),
        "Force pushing can overwrite remote history.",
    ),
]

DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)


def command_from_payload(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def project_path_from_payload(payload: dict) -> str:
    for key in ("cwd", "project_dir", "workspace_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def split_sql_statements(command: str) -> list[str]:
    return [statement.strip() for statement in command.split(";") if statement.strip()]


def delete_without_where(command: str) -> bool:
    for statement in split_sql_statements(command):
        if DELETE_FROM.search(statement) and not WHERE.search(statement):
            return True
    return False


def blocked_reason(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in PATTERNS:
        if pattern.search(command):
            return name, reason

    if delete_without_where(command):
        return "DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can remove every row in a table."

    return None


def log_block(payload: dict, command: str, pattern_name: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "pattern": pattern_name,
        "reason": reason,
        "project_path": project_path_from_payload(payload),
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(pattern_name: str, reason: str) -> None:
    message = (
        f"Dangerous Bash command blocked ({pattern_name}). {reason} "
        f"The attempt was logged to {LOG_PATH}."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = command_from_payload(payload)
    if not command:
        return 0

    match = blocked_reason(command)
    if match is None:
        return 0

    pattern_name, reason = match
    log_block(payload, command, pattern_name, reason)
    deny(pattern_name, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
