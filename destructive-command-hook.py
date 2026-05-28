#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands.

Install under ~/.claude/hooks/ and register it for Bash PreToolUse events.
The hook reads Claude Code's JSON event from stdin and exits non-zero when the
attempted Bash command matches a dangerous pattern.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("rm -rf", re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|- [^\n]*|-[A-Za-z]*f[A-Za-z]*r)\b", re.I), "recursive forced delete"),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I), "SQL table drop"),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=|-with-lease)", re.I), "forced git push"),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.I), "SQL truncate"),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b|;|\n).)*(?:;|$)", re.I | re.S),
        "SQL delete without WHERE clause",
    ),
]


def extract_command(payload: dict[str, Any]) -> str:
    """Handle common Claude Code hook payload shapes."""
    candidates = [
        payload.get("command"),
        payload.get("tool_input", {}).get("command") if isinstance(payload.get("tool_input"), dict) else None,
        payload.get("input", {}).get("command") if isinstance(payload.get("input"), dict) else None,
        payload.get("parameters", {}).get("command") if isinstance(payload.get("parameters"), dict) else None,
    ]
    for value in candidates:
        if isinstance(value, str):
            return value
    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "repository"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_block(command: str, project: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp}\t{project}\t{reason}\t{safe_command}\n")


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"command": raw}

    command = extract_command(payload)
    if not command:
        return 0

    for name, pattern, reason in PATTERNS:
        if pattern.search(command):
            project = project_path(payload)
            log_block(command, project, name)
            print(
                f"Blocked destructive Bash command: {reason}. Pattern: {name}. "
                f"No command was run. Logged to {LOG_PATH}.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
