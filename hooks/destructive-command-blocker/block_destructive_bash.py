#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("recursive force deletion with rm -rf", re.compile(r"\brm\s+-(?:[^\s-]*[rf][^\s-]*|[rf]{1,2})\b", re.I)),
    ("destructive database command: DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("force push with git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)", re.I)),
    ("destructive database command: TRUNCATE", re.compile(r"\btruncate\b", re.I)),
    ("DELETE FROM without a WHERE clause", re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.I | re.S)),
]


def read_hook_input() -> dict:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return {}

    try:
        return json.loads(raw_input)
    except json.JSONDecodeError:
        return {}


def bash_command(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def project_path(payload: dict) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project_dir:
        return env_project_dir

    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason
    return None


def log_blocked_attempt(command: str, reason: str, project: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    safe_project = project.replace("\r", "\\r").replace("\n", "\\n")

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{reason}\t{safe_project}\t{safe_command}\n")


def main() -> int:
    payload = read_hook_input()
    command = bash_command(payload)

    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project = project_path(payload)
    log_blocked_attempt(command, reason, project)

    print(
        "Blocked unsafe Bash command before execution.\n"
        f"Reason: {reason}.\n"
        "Choose a safer command, inspect the target path first, or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

