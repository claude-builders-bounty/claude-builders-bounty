#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES = [
    ("rm -rf", re.compile(r"(?:^|[;&|()\s])rm\s+(?:-[^\s]*r[^\s]*f|-f[^\s]*r|-[^\s]*R[^\s]*f|-f[^\s]*R)\b", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b).)*(?:;|$)", re.IGNORECASE | re.DOTALL)),
]


def _read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"PreToolUse blocker could not parse hook input as JSON: {exc}", file=sys.stderr)
        return {}


def _extract_command(event: dict) -> str:
    tool_input = event.get("tool_input") or event.get("input") or {}
    if not isinstance(tool_input, dict):
        return ""

    for key in ("command", "cmd", "script"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def _project_path(event: dict) -> str:
    cwd = event.get("cwd") or event.get("project_path") or event.get("workspace")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.getcwd()


def _blocked_reason(command: str) -> str | None:
    for label, pattern in BLOCK_RULES:
        if pattern.search(command):
            return label
    return None


def _log_block(reason: str, command: str, project_path: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    safe_command = command.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{project_path}\t{reason}\t{safe_command}\n")


def main() -> int:
    event = _read_event()
    tool_name = str(event.get("tool_name") or event.get("tool") or "")

    if tool_name and tool_name not in {"Bash", "bash"}:
        return 0

    command = _extract_command(event)
    if not command:
        return 0

    reason = _blocked_reason(command)
    if not reason:
        return 0

    project_path = _project_path(event)
    _log_block(reason, command, project_path)
    print(
        "Blocked dangerous bash command before execution. "
        f"Matched rule: {reason}. Review the command and choose a safer alternative.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
