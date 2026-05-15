#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the Claude Code hook JSON payload from stdin and emits a PreToolUse
permission denial when a Bash command matches a destructive pattern.
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
        re.compile(r"(^|[;&|()\s])rm\s+(?:-[^\s;|&]*r[^\s;|&]*f|-f[^\s;|&]*r|-r[^\s;|&]*\s+-f|-f\s+-r)(?=\s|$)", re.IGNORECASE),
        "Recursive forced removal can delete large parts of the project or system.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE permanently removes a database table.",
    ),
    (
        "git push --force",
        re.compile(r"(^|[;&|()\s])git\s+push\b[^\n;|&]*(?:--force\b|-f\b|--force-with-lease\b)", re.IGNORECASE),
        "Force-pushing can rewrite shared Git history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE deletes all rows from a table.",
    ),
]

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def strip_sql_comments(command: str) -> str:
    command = re.sub(r"--.*?(?=\n|$)", " ", command)
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    return command


def split_sql_statements(command: str) -> list[str]:
    # This intentionally stays simple: the target is Bash commands, not a full SQL parser.
    return [part.strip() for part in command.split(";") if part.strip()]


def find_block_reason(command: str) -> tuple[str, str] | None:
    for label, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return label, reason

    sql_without_comments = strip_sql_comments(command)
    for statement in split_sql_statements(sql_without_comments):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can delete every row in a table."

    return None


def log_block(command: str, cwd: str, label: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": cwd,
        "pattern": label,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed hook input should not break normal Claude Code execution.
        return 0

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    matched = find_block_reason(command)
    if not matched:
        return 0

    label, explanation = matched
    cwd = str(payload.get("cwd") or os.getcwd())
    log_block(command=command, cwd=cwd, label=label)
    deny(
        "Destructive Bash command blocked by Claude Code safety hook: "
        f"matched {label}. {explanation} Rewrite the command to use a safer, scoped operation "
        "or ask the user for explicit manual approval outside the hook."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
