#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKERS = [
    ("rm -rf", re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b")),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b.*(?:--force|-f)\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
]

DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bwhere\b", re.IGNORECASE)


def load_event() -> dict[str, Any]:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def blocked_reason(command: str) -> str | None:
    for reason, pattern in BLOCKERS:
        if pattern.search(command):
            return reason

    if DELETE_FROM.search(command) and not WHERE_CLAUSE.search(command):
        return "DELETE FROM without WHERE"

    return None


def log_blocked_attempt(command: str, cwd: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "command": command,
        "project_path": cwd,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    event = load_event()
    if event.get("hook_event_name") != "PreToolUse":
        return 0
    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    cwd = str(event.get("cwd") or "")

    reason = blocked_reason(command)
    if not reason:
        return 0

    log_blocked_attempt(command, cwd)
    print(
        "Blocked dangerous Bash command before execution: "
        f"{reason}. Attempted command: {command}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
