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


HOOK_EVENT_NAME = "PreToolUse"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RF_PATTERN = re.compile(
    r"(?ix)"
    r"(?:^|[;&|]\s*)"
    r"(?:sudo\s+|command\s+)?"
    r"(?:/usr/bin/|/bin/)?rm\s+"
    r"(?:"
    r"(?=[^;&|]*-[A-Za-z]*r)(?=[^;&|]*-[A-Za-z]*f)"
    r"|"
    r"(?=[^;&|]*--recursive)(?=[^;&|]*--force)"
    r")"
)

GIT_FORCE_PUSH_PATTERN = re.compile(
    r"(?ix)"
    r"(?:^|[;&|]\s*)"
    r"(?:sudo\s+|command\s+)?"
    r"git\s+push\b"
    r"(?=[^;&|]*(?:--force(?:-with-lease|-if-includes)?|-f)\b)"
)

SQL_CLIENT_PATTERN = re.compile(
    r"(?ix)"
    r"(?:^|[;&|]\s*)"
    r"(?:psql|mysql|mariadb|sqlite3|sqlcmd|duckdb|clickhouse-client|dbmate|prisma|sequelize|knex)\b"
)

DROP_TABLE_PATTERN = re.compile(r"(?is)\bdrop\s+table\b")
TRUNCATE_PATTERN = re.compile(r"(?is)\btruncate(?:\s+table)?\b")
DELETE_FROM_PATTERN = re.compile(r"(?is)\bdelete\s+from\b")
WHERE_PATTERN = re.compile(r"(?is)\bwhere\b")


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or ""
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _sql_statement_is_risky(command: str) -> tuple[bool, str | None]:
    if not SQL_CLIENT_PATTERN.search(command):
        return False, None

    if DROP_TABLE_PATTERN.search(command):
        return True, "DROP TABLE statements can permanently remove schema and data."

    if TRUNCATE_PATTERN.search(command):
        return True, "TRUNCATE statements can irreversibly remove all rows."

    if DELETE_FROM_PATTERN.search(command) and not WHERE_PATTERN.search(command):
        return True, "DELETE FROM without a WHERE clause can remove an entire table."

    return False, None


def find_block_reason(command: str) -> str | None:
    """Return a human-readable reason if the Bash command should be blocked."""
    if RM_RF_PATTERN.search(command):
        return "rm -rf style recursive forced deletion is blocked."

    if GIT_FORCE_PUSH_PATTERN.search(command):
        return "git push --force can rewrite shared history and is blocked."

    sql_risky, sql_reason = _sql_statement_is_risky(command)
    if sql_risky:
        return sql_reason

    return None


def _write_log(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "attempted_command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(reason: str, command: str) -> None:
    message = (
        f"Blocked destructive Bash command: {reason} "
        "Review the command, choose a safer alternative, or ask the user for explicit guidance."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    json.dump(output, sys.stdout)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive-command-guard: invalid JSON input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    _write_log(command, _project_path(payload), reason)
    _deny(reason, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
