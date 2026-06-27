#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf can delete whole directory trees",
        re.compile(r"(?i)(?:^|[;&|()\s])rm\s+(?:-[\w-]*r[\w-]*f|-[\w-]*f[\w-]*r)\b"),
    ),
    ("DROP TABLE can destroy database tables", re.compile(r"(?i)\bdrop\s+table\b")),
    (
        "git push --force rewrites shared history",
        re.compile(r"(?i)\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)"),
    ),
    ("TRUNCATE can erase database table contents", re.compile(r"(?i)\btruncate\b")),
    (
        "DELETE FROM without WHERE can delete every row",
        re.compile(r"(?is)\bdelete\s+from\b(?:(?!\bwhere\b)[^;])*;?\s*$"),
    ),
)


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    for key in ("command", "cmd", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd")
        if isinstance(value, str) and value:
            return value

    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    for reason, pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def log_blocked_attempt(command: str, project_path: str, log_path: Path | None = None) -> None:
    destination = log_path or Path.home() / ".claude" / "hooks" / "blocked.log"
    destination.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with destination.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{project_path}\t{safe_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Hook input was not valid JSON, so no command was blocked.", file=sys.stderr)
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    log_blocked_attempt(command, project_path)
    print(f"Blocked destructive bash command: {reason}.", file=sys.stderr)
    print("Review the command and run a safer alternative instead.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
