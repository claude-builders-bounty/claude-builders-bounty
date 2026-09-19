#!/usr/bin/env python3
"""Claude Code PreToolUse guard for dangerous shell commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))


def command_from(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def reason_for(command: str) -> str | None:
    checks = (
        (r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*(?:\s|$)", "rm -rf can delete files recursively"),
        (r"\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*(?:\s|$)", "rm -rf can delete files recursively"),
        (r"\bDROP\s+TABLE\b", "DROP TABLE can destroy a database table"),
        (r"\bgit\s+push\b[^\n;|&]*\s(?:--force|-f)(?:\s|$)", "forced git pushes can overwrite shared history"),
        (r"\bTRUNCATE(?:\s+TABLE)?\b", "TRUNCATE can remove all rows from a table"),
    )
    for pattern, reason in checks:
        if re.search(pattern, command, re.IGNORECASE):
            return reason

    delete = re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE)
    if delete and not re.search(r"\bWHERE\b", command[delete.end() :], re.IGNORECASE):
        return "DELETE FROM without WHERE can remove every row"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        payload = {}

    command = command_from(payload)
    reason = reason_for(command)
    if reason is None:
        return 0

    project = payload.get("cwd") or os.getcwd()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\t{project}\t{command}\n")

    message = f"Blocked dangerous command: {reason}. Review it and run it manually only if intentional."
    print(json.dumps({"decision": "deny", "reason": message}))
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
