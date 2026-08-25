#!/usr/bin/env python3
"""PreToolUse hook: block destructive bash/SQL commands before execution."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+", re.I), "rm -rf"),
    (re.compile(r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+", re.I), "rm -rf"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE"),
    (re.compile(r"\bgit\s+push\b.*(\s--force\b|\s-f\b)", re.I), "git push --force"),
    (
        re.compile(r"\bDELETE\s+FROM\s+\w+\s*(?:;|\s*$)", re.I),
        "DELETE FROM without WHERE",
    ),
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def match_blocked(command: str) -> str | None:
    for pattern, label in BLOCKED_PATTERNS:
        if pattern.search(command):
            return label
    return None


def log_blocked(command: str, reason: str, project_path: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "reason": reason,
        "project_path": project_path,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Bash", "PowerShell"):
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command", "")
    if not command:
        sys.exit(0)

    blocked = match_blocked(command)
    if not blocked:
        sys.exit(0)

    project_path = data.get("cwd") or data.get("session_id") or "."
    reason = (
        f"Blocked destructive command ({blocked}). "
        f"This hook prevents accidental data loss. "
        f"Command was not executed."
    )
    log_blocked(command, reason, project_path)
    deny(reason)


if __name__ == "__main__":
    main()
