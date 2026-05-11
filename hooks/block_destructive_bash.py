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


class BlockReason:
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def _sql_candidates(command: str) -> list[str]:
    candidates: list[str] = []

    if re.match(r"^\s*(drop\s+table|truncate\b|delete\s+from\b)", command, re.IGNORECASE):
        candidates.append(command)

    for match in re.finditer(
        r"(?:^|\s)(?:-c|-e|--execute(?:=|\s+))\s*(['\"])(.*?)\1",
        command,
        re.IGNORECASE | re.DOTALL,
    ):
        candidates.append(match.group(2))

    return candidates


def _sql_statements(sql: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n", sql) if part.strip()]


def _delete_without_where(sql: str) -> bool:
    for statement in _sql_statements(sql):
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, re.IGNORECASE
        ):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    checks: list[tuple[re.Pattern[str], BlockReason]] = [
        (
            re.compile(r"\brm\s+-(?=[A-Za-z]*r)(?=[A-Za-z]*f)[A-Za-z]*\b"),
            BlockReason("rm-rf", "`rm -rf` style recursive force deletion is blocked."),
        ),
        (
            re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)"),
            BlockReason("git-push-force", "`git push --force` is blocked."),
        ),
    ]

    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    for sql in _sql_candidates(command):
        if re.search(r"\bdrop\s+table\b", sql, re.IGNORECASE):
            return BlockReason("drop-table", "`DROP TABLE` is blocked.")
        if re.search(r"\btruncate\b", sql, re.IGNORECASE):
            return BlockReason("truncate", "`TRUNCATE` is blocked.")
        if _delete_without_where(sql):
            return BlockReason(
                "delete-without-where",
                "`DELETE FROM` without a `WHERE` clause is blocked.",
            )

    return None


def log_blocked(command: str, cwd: str, reason: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_cwd = cwd.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp}\t{reason.code}\tproject={safe_cwd}\tcommand={safe_command}\n"
        )


def read_hook_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block_destructive_bash: invalid hook JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    payload = read_hook_input()

    if payload.get("hook_event_name") != "PreToolUse":
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    cwd = str(payload.get("cwd") or os.getcwd())
    log_blocked(command, cwd, reason)
    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {reason.message}\n"
        f"Project: {cwd}\n"
        "If this action is intentional, ask the user for explicit approval and use a safer, targeted command.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
