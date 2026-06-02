#!/usr/bin/env python3
"""Claude Code PreToolUse hook that denies destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rm -rf", re.compile(r"(^|[;&|]\s*)rm\s+(-[^\s]*r[^\s]*f|-?[^\s]*f[^\s]*r)\b")),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(--force|-f)\b")),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\b(?![^;]*\bwhere\b)", re.IGNORECASE)),
)


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def command_from(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def find_match(command: str) -> str | None:
    for label, pattern in PATTERNS:
        if pattern.search(command):
            return label
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    override = os.environ.get("CLAUDE_BLOCKED_LOG_PATH")
    if override:
        log_path = Path(override).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        hook_dir = Path.home() / ".claude" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        log_path = hook_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", " ").replace("\n", "\\n")
    line = f"{timestamp}\t{project_path}\t{reason}\t{safe_command}\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> int:
    payload = read_input()
    command = command_from(payload)
    if not command:
        return 0

    match = find_match(command)
    if not match:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    reason = f"Blocked destructive Bash command pattern: {match}."
    log_block(command, project_path, match)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
