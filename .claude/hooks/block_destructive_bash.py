#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks dangerous Bash commands."""

from __future__ import annotations

import datetime as _datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


DESTRUCTIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive force removal with rm -rf", re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b")),
    ("recursive force removal with rm -fr", re.compile(r"\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b")),
    ("forced git push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)")),
    ("DROP TABLE statement", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("TRUNCATE statement", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    command = payload.get("command")
    if isinstance(command, str):
        return command

    return ""


def _extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "workspace_path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value

    return os.getcwd()


def _delete_from_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE) and not re.search(
            r"\bWHERE\b", statement, re.IGNORECASE
        ):
            return True
    return False


def find_block_reason(command: str) -> Optional[str]:
    if not command.strip():
        return None

    for reason, pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return reason

    if _delete_from_without_where(command):
        return "DELETE FROM statement without a WHERE clause"

    return None


def _append_log(command: str, project_path: str, reason: str, log_path: Path = LOG_PATH) -> None:
    timestamp = _datetime.datetime.now(_datetime.UTC).isoformat()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "attempted_command": command,
                    "project_path": project_path,
                    "reason": reason,
                },
                ensure_ascii=True,
            )
            + "\n"
        )


def evaluate(payload: dict[str, Any], log_path: Path = LOG_PATH) -> tuple[bool, str]:
    tool_name = payload.get("tool_name") or payload.get("tool")
    if tool_name not in (None, "Bash", "bash"):
        return False, ""

    command = _extract_command(payload)
    reason = find_block_reason(command)
    if reason is None:
        return False, ""

    project_path = _extract_project_path(payload)
    _append_log(command, project_path, reason, log_path)
    return True, (
        "Blocked destructive Bash command: "
        f"{reason}. Rewrite the command with a safer, narrower operation before continuing."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Invalid hook input JSON: {error}", file=sys.stderr)
        return 2

    blocked, message = evaluate(payload)
    if blocked:
        print(message, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
