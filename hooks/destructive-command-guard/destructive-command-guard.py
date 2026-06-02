#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DENY_EVENT = "PreToolUse"


def normalize_sql(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip().upper()


def rm_rf_reason(command: str) -> str | None:
    for match in re.finditer(r"(?:^|[;&|()\s])rm\s+([^;&|()]+)", command):
        args = match.group(1).split()
        for arg in args:
            if arg.startswith("-") and "r" in arg and "f" in arg:
                return "recursive forced removal is not allowed"
    return None


def delete_without_where_reason(command: str) -> str | None:
    sql = normalize_sql(command)
    for statement in re.split(r";+", sql):
        if re.search(r"\bDELETE\s+FROM\b", statement) and not re.search(r"\bWHERE\b", statement):
            return "DELETE FROM without a WHERE clause is not allowed"
    return None


def blocked_reason(command: str) -> str | None:
    checks = [
        rm_rf_reason(command),
        "force-pushing git history is not allowed"
        if re.search(r"\bgit\s+push\b[^\n;|&]*\s--force(?:-with-lease)?\b", command)
        else None,
        "DROP TABLE statements are not allowed"
        if re.search(r"\bDROP\s+TABLE\b", normalize_sql(command))
        else None,
        "TRUNCATE statements are not allowed"
        if re.search(r"\bTRUNCATE\b", normalize_sql(command))
        else None,
        delete_without_where_reason(command),
    ]
    return next((reason for reason in checks if reason), None)


def project_path(payload: dict) -> str:
    return (
        payload.get("cwd")
        or payload.get("project_dir")
        or payload.get("workspace_dir")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(command: str, path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_path.open("a", encoding="utf-8").write(
        f"{timestamp}\tproject={path}\treason={reason}\tcommand={command!r}\n"
    )


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": DENY_EVENT,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked destructive Bash command: {reason}.",
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    log_block(command, project_path(payload), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
