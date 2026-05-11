#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def normalize_sql(command: str) -> str:
    return re.sub(r"\s+", " ", command)


def has_delete_without_where(command: str) -> bool:
    sql = normalize_sql(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement = sql[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks = [
        (
            re.compile(
                r"(^|[;&|]\s*)rm\s+-(?=[^\s;&|]*r)(?=[^\s;&|]*f)[^\s;&|]*",
                re.IGNORECASE,
            ),
            "rm -rf style recursive force deletion is blocked",
        ),
        (
            re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
            "DROP TABLE is blocked because it can destroy database schema",
        ),
        (
            re.compile(r"\bgit\s+push\b[^\n;&|]*(--force|-f)\b", re.IGNORECASE),
            "git push --force is blocked because it can rewrite shared history",
        ),
        (
            re.compile(r"\btruncate\b", re.IGNORECASE),
            "TRUNCATE is blocked because it can erase table contents",
        ),
    ]

    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    if has_delete_without_where(command):
        return "DELETE FROM without a WHERE clause is blocked"

    return None


def project_path(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_dir"),
        payload.get("workspace"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.getcwd(),
    ]
    return next((str(value) for value in candidates if value), "unknown")


def log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path(payload),
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked destructive Bash command: "
                        f"{reason}. Rewrite the command to use a safer, reversible operation."
                    ),
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block_destructive_bash.py: invalid JSON input: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = blocked_reason(command)
    if not reason:
        return 0

    log_block(payload, command, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
