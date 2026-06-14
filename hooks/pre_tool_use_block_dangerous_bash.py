#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_PATTERNS = (
    ("rm -rf", re.compile(r"\brm\s+-[^\s;|&]*r[^\s;|&]*f[^\s;|&]*\b", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$)", re.IGNORECASE)),
)

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def home_dir() -> Path:
    return Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or "~").expanduser()


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def command_from_payload(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def blocked_reason(command: str) -> str | None:
    for label, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return label

    delete_match = DELETE_FROM_RE.search(command)
    if delete_match and not WHERE_RE.search(command, delete_match.end()):
        return "DELETE FROM without WHERE"

    return None


def append_block_log(command: str, project_path: str, reason: str) -> None:
    log_dir = home_dir() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"{timestamp}\treason={reason}\tproject={project_path}\tcommand={command}\n"
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def main() -> int:
    payload = load_payload()
    command = command_from_payload(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    append_block_log(command, project_path, reason)
    print(
        f"Blocked destructive Bash command ({reason}): {command}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
