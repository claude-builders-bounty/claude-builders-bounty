#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands.

Reads a Claude Code hook JSON payload from stdin. If the payload is for the
Bash tool and the command matches a destructive pattern, logs the blocked
attempt and exits 2 so Claude Code blocks the tool call.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+[^\n;|&]*-[^\n;|&]*r[^\n;|&]*f|\brm\s+[^\n;|&]*-[^\n;|&]*f[^\n;|&]*r", re.I), "rm -rf"),
    (re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=)|\bgit\s+push\b[^\n;|&]*\s-f(?:\b|\s)", re.I), "git push --force"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE"),
]

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.I)
WHERE_RE = re.compile(r"\bWHERE\b", re.I)


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            return tool_input
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    return command if isinstance(command, str) else ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")
    return tool_name.lower() == "bash"


def destructive_reason(command: str) -> str | None:
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return "DELETE FROM without WHERE"
    return None


def project_path(payload: dict[str, Any]) -> str:
    value = payload.get("project_dir") or payload.get("cwd") or os.getcwd()
    return str(value)


def log_blocked_attempt(command: str, project: str, reason: str) -> Path:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp}\t{project}\t{reason}\t{command}\n")
    return log_file


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict) or not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    reason = destructive_reason(command)
    if reason is None:
        return 0

    project = project_path(payload)
    log_file = log_blocked_attempt(command, project, reason)
    print(
        f"Blocked destructive command ({reason}). "
        f"Attempt was logged to {log_file}. Command: {command}"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
