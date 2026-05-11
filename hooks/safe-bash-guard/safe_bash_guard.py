#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable


BLOCK_LOG = Path(os.environ.get("CLAUDE_SAFE_BASH_GUARD_LOG", Path.home() / ".claude" / "hooks" / "blocked.log"))


RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "recursive force deletion",
        re.compile(
            r"(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)",
            re.IGNORECASE,
        ),
        "Blocked recursive force deletion. Use a narrower, reviewable removal command instead of rm -rf.",
    ),
    (
        "force push",
        re.compile(
            r"(?:^|[;&|]\s*)git\s+push\b(?=[^;&|]*(?:--force(?:-with-lease)?|-f(?:\s|$)))",
            re.IGNORECASE,
        ),
        "Blocked force push. Use a normal push or ask the user before rewriting remote history.",
    ),
    (
        "drop table",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "Blocked DROP TABLE. Ask for explicit human confirmation before destructive schema changes.",
    ),
    (
        "truncate",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "Blocked TRUNCATE. Ask for explicit human confirmation before deleting table contents.",
    ),
)

DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)


def iter_sql_statements(command: str) -> Iterable[str]:
    for statement in re.split(r";|\n\s*\n", command):
        statement = statement.strip()
        if statement:
            yield statement


def find_block_reason(command: str) -> tuple[str, str] | None:
    for reason, pattern, message in RULES:
        if pattern.search(command):
            return reason, message

    for statement in iter_sql_statements(command):
        if DELETE_FROM.search(statement) and not WHERE.search(statement):
            return (
                "delete without where",
                "Blocked DELETE FROM without WHERE. Add a WHERE clause or ask the user before bulk deletion.",
            )

    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with BLOCK_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def deny(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                },
                "suppressOutput": True,
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    if not command:
        return 0

    result = find_block_reason(command)
    if result is None:
        return 0

    reason, message = result
    project_path = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or "")
    log_block(command, project_path, reason)
    deny(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
