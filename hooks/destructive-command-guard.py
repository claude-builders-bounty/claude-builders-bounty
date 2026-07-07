#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


BLOCKERS = (
    (
        "rm -rf",
        re.compile(r"(^|[;&|()\s])(?:sudo\s+)?rm\s+-(?=[A-Za-z]*r)(?=[A-Za-z]*f)[A-Za-z]+(?:\s|$)"),
        "`rm -rf` recursively deletes files and is blocked by the destructive command guard.",
    ),
    (
        "git push --force",
        re.compile(r"(^|[;&|()\s])git\s+push\b[^\n;&|]*(?:\s-f(?:\s|$)|\s--force(?:\s|=|$)|\s--force-with-lease(?:\s|=|$))"),
        "`git push --force` or an equivalent force push rewrites remote history and is blocked by the destructive command guard.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "`DROP TABLE` can destroy schema data and is blocked by the destructive command guard.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "`TRUNCATE` can erase table data and is blocked by the destructive command guard.",
    ),
)


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def get_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def split_sql_statements(command: str) -> list[str]:
    return [statement.strip() for statement in command.split(";") if statement.strip()]


def has_delete_without_where(command: str) -> bool:
    for statement in split_sql_statements(command):
        delete_match = re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE)
        if not delete_match:
            continue

        tail = statement[delete_match.end() :]
        if not re.search(r"\bWHERE\b", tail, re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    for _name, pattern, reason in BLOCKERS:
        if pattern.search(command):
            return reason

    if has_delete_without_where(command):
        return "`DELETE FROM` without a `WHERE` clause is blocked by the destructive command guard."

    return None


def project_path(payload: dict) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project_dir:
        return env_project_dir
    return os.getcwd()


def log_blocked_attempt(command: str, payload: dict) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path(payload),
        "attempted_command": command,
        "command": command,
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
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> int:
    payload = read_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    command = get_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    log_blocked_attempt(command, payload)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
