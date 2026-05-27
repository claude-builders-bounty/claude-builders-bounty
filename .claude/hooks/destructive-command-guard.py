#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


BLOCK_RULES = (
    (
        "recursive forced removal",
        re.compile(r"(?is)(?:^|[;&|]\s*)rm\s+(?=[^\n;&|]*-[^\n;&|]*r)(?=[^\n;&|]*-[^\n;&|]*f)[^\n;&|]*"),
    ),
    ("DROP TABLE statement", re.compile(r"(?is)\bdrop\s+table\b")),
    ("forced git push", re.compile(r"(?is)\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b")),
    ("TRUNCATE statement", re.compile(r"(?is)\btruncate\b")),
    (
        "DELETE FROM without WHERE",
        re.compile(r"(?is)\bdelete\s+from\b(?:(?!\bwhere\b|;).)*($|;)"),
    ),
)


def load_event() -> dict:
    try:
        raw_input = sys.stdin.read()
        return json.loads(raw_input) if raw_input.strip() else {}
    except json.JSONDecodeError:
        return {}


def get_command(event: dict) -> str:
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def project_path(event: dict) -> str:
    for key in ("cwd", "project_dir", "projectPath", "workspace", "workspace_dir"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def first_block_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason
    return None


def append_block_log(command: str, path: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": path,
        "reason": reason,
        "command": command,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason}. Rewrite the command so it cannot destroy data or history."
            ),
        }
    }
    print(json.dumps(response))


def main() -> int:
    event = load_event()
    command = get_command(event)
    reason = first_block_reason(command)

    if not reason:
        return 0

    append_block_log(command, project_path(event), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
