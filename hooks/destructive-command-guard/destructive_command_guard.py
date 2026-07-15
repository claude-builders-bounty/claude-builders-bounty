#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks dangerous Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "recursive forced removal",
        re.compile(r"(^|[;&|]\s*)rm\s+(?:-[^\s]*r[^\s]*f|-f[^\s]*r)\b", re.IGNORECASE),
        "rm -rf can permanently delete project or system files.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b", re.IGNORECASE),
        "force pushing can rewrite shared history.",
    ),
    (
        "drop table",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE destroys database schema and data.",
    ),
    (
        "truncate table",
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
        "TRUNCATE removes all rows from a table.",
    ),
    (
        "delete without where",
        re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.IGNORECASE),
        "DELETE FROM without WHERE can remove every row.",
    ),
)


def load_event() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        event = json.loads(raw)
        return event if isinstance(event, dict) else {}
    except json.JSONDecodeError:
        return {}


def command_from_event(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    inputs = event.get("inputs")
    if isinstance(inputs, dict):
        command = inputs.get("command")
        if isinstance(command, str):
            return command

    command = event.get("command")
    return command if isinstance(command, str) else ""


def project_path_from_event(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "workspace_path"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def blocked_reason(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return name, reason
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project = project_path.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{safe_project}\t{reason}\t{safe_command}\n")


def main() -> int:
    event = load_event()
    command = command_from_event(event)
    if not command:
        return 0

    match = blocked_reason(command)
    if match is None:
        return 0

    name, reason = match
    project_path = project_path_from_event(event)
    log_block(command, project_path, name)
    print(
        "Blocked dangerous Bash command before execution.\n"
        f"Reason: {reason}\n"
        f"Command: {command}\n"
        "Choose a safer command or ask the user for an explicit recovery plan.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
