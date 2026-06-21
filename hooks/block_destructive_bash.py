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


BLOCK_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\brm\s+(?:-[^\s]*[rf][^\s]*|-[^\s]*r[^\s]*\s+-[^\s]*f[^\s]*)\b", re.I), "rm -rf"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE"),
    (re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$)", re.I), "git push --force"),
)

DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.I)
WHERE = re.compile(r"\bWHERE\b", re.I)


def home_dir() -> Path:
    return Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or str(Path.home()))


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    for pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return reason

    if DELETE_FROM.search(command) and not WHERE.search(command):
        return "DELETE FROM without a WHERE clause"

    return None


def write_block_log(command: str, project_path: str, reason: str) -> None:
    log_path = home_dir() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    safe_project_path = project_path.replace("\r", "\\r").replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as log:
        log.write(
            f"{timestamp}\treason={reason}\tproject={safe_project_path}\tcommand={safe_command}\n"
        )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = extract_command(payload)
    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    write_block_log(command, project_path, reason)
    print(
        "Blocked dangerous Bash command before execution.\n"
        f"Reason: matched `{reason}`.\n"
        "This command can delete data, rewrite shared history, or destroy database tables. "
        "Use a safer, explicit command or ask the user for a narrower operation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
