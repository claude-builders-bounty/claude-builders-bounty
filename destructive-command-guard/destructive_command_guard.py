#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks a small destructive-command policy."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RM = re.compile(r"(?:^|[;&|]\s*)rm\b(?=[^;&|]*\s-(?:[A-Za-z]*r[A-Za-z]*f|[A-Za-z]*f[A-Za-z]*r)(?:\s|$))", re.I)
RM_LONG = re.compile(r"(?:^|[;&|]\s*)rm\s+(?=[^;&|]*--recursive\b)(?=[^;&|]*--force\b)", re.I)
FORCE_PUSH = re.compile(r"(?:^|[;&|]\s*)git\s+push\b[^;&|]*(?:\s--force(?:-with-lease|-if-includes)?\b|\s-f(?:\s|$))", re.I)
DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.I)
SQL_TRUNCATE = re.compile(r"\btruncate\s+(?:table\s+)?(?:only\s+)?[A-Za-z_\"`]", re.I)
DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.I)
WHERE = re.compile(r"\bwhere\b", re.I)


def blocked_reason(command: str) -> str | None:
    if RM.search(command) or RM_LONG.search(command):
        return "recursive forced deletion (rm -rf)"
    if FORCE_PUSH.search(command):
        return "forced Git push"
    if DROP_TABLE.search(command):
        return "DROP TABLE statement"
    if SQL_TRUNCATE.search(command):
        return "TRUNCATE statement"
    # Evaluate each SQL statement independently: a WHERE in a later statement
    # must not make an earlier unbounded DELETE look safe.
    for statement in command.split(";"):
        match = DELETE_FROM.search(statement)
        if match and not WHERE.search(statement[match.end():]):
            return "DELETE FROM statement without a WHERE clause"
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    directory = Path.home() / ".claude" / "hooks"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / "blocked.log"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        print("Invalid hook input; refusing Bash execution", file=sys.stderr)
        return 2
    if event.get("tool_name") != "Bash":
        return 0
    command = str((event.get("tool_input") or {}).get("command") or "")
    reason = blocked_reason(command)
    if not reason:
        return 0
    project_path = str(event.get("cwd") or os.getcwd())
    log_block(command, project_path, reason)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked {reason}. The attempt was logged to "
                "~/.claude/hooks/blocked.log. Use a bounded, reversible command instead."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
