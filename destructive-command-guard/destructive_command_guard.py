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


BLOCK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf style recursive forced deletion",
        re.compile(
            r"(^|[;&|()\n]\s*)rm\s+("
            r"-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b|"
            r"-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b|"
            r"(--recursive|-r)\s+(--force|-f)\b|"
            r"(--force|-f)\s+(--recursive|-r)\b"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "forced git push",
        re.compile(
            r"(^|[;&|()\n]\s*)git\s+push\b[^\n;&|]*\s"
            r"(--force(?:=\S+)?|--force-with-lease|-f)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "DROP TABLE statement",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    ),
    (
        "TRUNCATE statement",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
    ),
)

DELETE_FROM_RE = re.compile(
    r"\bdelete\s+from\b(?P<body>.*?)(?:;|$)",
    re.IGNORECASE | re.DOTALL,
)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def find_block_reason(command: str) -> str | None:
    """Return the first destructive pattern found in a Bash command."""
    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason

    for match in DELETE_FROM_RE.finditer(command):
        statement = match.group(0)
        if not WHERE_RE.search(statement):
            return "DELETE FROM statement without WHERE clause"

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    hooks_dir = Path(os.environ.get("CLAUDE_HOOKS_DIR", Path.home() / ".claude" / "hooks"))
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    message = (
        "Destructive Bash command blocked by destructive-command-guard: "
        f"{reason}. Rewrite the command to be safer or ask the user explicitly."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked_attempt(command, project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
