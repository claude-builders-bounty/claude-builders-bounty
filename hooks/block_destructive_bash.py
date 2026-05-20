#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


BLOCK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?is)\brm\s+(?:(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*)|(?:-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*))\b"),
        "recursive force removal with rm -rf/rm -fr",
    ),
    (
        re.compile(r"(?is)\brm\s+(?:-[A-Za-z]*r[A-Za-z]*\s+-[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*\s+-[A-Za-z]*r[A-Za-z]*)\b"),
        "recursive force removal with rm -r -f/rm -f -r",
    ),
    (
        re.compile(r"(?is)\bgit\s+push\b[^\n;|&]*?(?:--force(?:-with-lease)?\b|-f\b)"),
        "force-pushing with git push --force/-f",
    ),
    (
        re.compile(r"(?is)\bDROP\s+TABLE\b"),
        "DROP TABLE statement",
    ),
    (
        re.compile(r"(?is)\bTRUNCATE(?:\s+TABLE)?\b"),
        "TRUNCATE statement",
    ),
)

DELETE_FROM_PATTERN = re.compile(r"(?is)\bDELETE\s+FROM\b")
WHERE_PATTERN = re.compile(r"(?is)\bWHERE\b")


def _hook_log_path() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def _normalize_command(input_data: dict[str, Any]) -> str:
    tool_input = input_data.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n", command) if part.strip()]


def find_block_reason(command: str) -> str | None:
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason

    for statement in _statements(command):
        if DELETE_FROM_PATTERN.search(statement) and not WHERE_PATTERN.search(statement):
            return "DELETE FROM statement without a WHERE clause"

    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    log_path = _hook_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    message = (
        "Blocked destructive Bash command: "
        f"{reason}. Choose a safer, reversible command or ask the user for explicit confirmation."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(output))


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if input_data.get("hook_event_name") != "PreToolUse" or input_data.get("tool_name") != "Bash":
        return 0

    command = _normalize_command(input_data)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = str(input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    log_blocked(command, project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
