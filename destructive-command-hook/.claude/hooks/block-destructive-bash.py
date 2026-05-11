#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|`$()\s])rm\s+[^\n;&|]*-[^\n;&|]*r[^\n;&|]*f|(^|[;&|`$()\s])rm\s+[^\n;&|]*-[^\n;&|]*f[^\n;&|]*r", re.I),
        "Recursive force deletion is blocked because it can permanently remove large parts of the project or filesystem.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.I),
        "DROP TABLE is blocked because it can destroy database schema and data.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.I),
        "TRUNCATE is blocked because it can delete all rows from a table.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(--force|-f\b|--force-with-lease)", re.I),
        "Force-pushing is blocked because it can overwrite shared git history.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\s+[\w.\"`\[\]-]+(?:(?!\bwhere\b)[^;])*($|;)", re.I | re.S),
        "DELETE FROM without a WHERE clause is blocked because it can delete an entire table.",
    ),
]


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def get_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")
    return ""


def get_project_path(payload: dict) -> str:
    for key in ("cwd", "project_dir", "workspace", "session_cwd"):
        value = payload.get(key)
        if value:
            return str(value)
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def find_block(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in PATTERNS:
        if pattern.search(command):
            return name, reason
    return None


def log_block(command: str, project_path: str, pattern_name: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp}\t{project_path}\t{pattern_name}\t{safe_command}\n")


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> int:
    payload = read_payload()
    command = get_command(payload)
    if not command:
        return 0

    blocked = find_block(command)
    if not blocked:
        return 0

    pattern_name, reason = blocked
    project_path = get_project_path(payload)
    log_block(command, project_path, pattern_name)
    deny(f"Blocked dangerous Bash command ({pattern_name}). {reason} Use a safer, narrower command or ask the user for explicit manual approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
