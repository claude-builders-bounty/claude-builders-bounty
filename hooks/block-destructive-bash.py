#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"(?is)(?:^|[;&|]\s*)rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b"),
        "Recursive force deletion is blocked because it can destroy project files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"(?is)\bdrop\s+table\b"),
        "DROP TABLE is blocked because it can delete database schema and data.",
    ),
    (
        "git push --force",
        re.compile(r"(?is)\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)"),
        "git push --force is blocked because it can rewrite shared repository history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"(?is)\btruncate\b"),
        "TRUNCATE is blocked because it can delete table contents.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"(?is)\bdelete\s+from\b(?:(?!\bwhere\b|;).)*(?:;|$)"),
        "DELETE FROM without a WHERE clause is blocked because it can delete every row.",
    ),
)


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def get_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def find_block_reason(command: str) -> tuple[str, str] | None:
    for label, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return label, reason
    return None


def append_block_log(command: str, cwd: str, label: str) -> None:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    timestamp = dt.datetime.now(dt.UTC).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    safe_cwd = cwd.replace("\r", "\\r").replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{label}\t{safe_cwd}\t{safe_command}\n")


def main() -> int:
    payload = read_payload()
    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    command = get_command(payload)
    if not command:
        return 0

    blocked = find_block_reason(command)
    if blocked is None:
        return 0

    label, reason = blocked
    cwd = payload.get("cwd")
    project_path = cwd if isinstance(cwd, str) and cwd else os.getcwd()
    append_block_log(command, project_path, label)
    print(
        f"Blocked destructive Bash command ({label}). {reason} "
        "Use a safer command or ask the user for an explicit, narrow alternative.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
