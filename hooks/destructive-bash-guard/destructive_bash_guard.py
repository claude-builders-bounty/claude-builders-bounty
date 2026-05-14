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


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def shell_words(command: str) -> list[str]:
    return re.findall(r"[^\s]+", command.strip())


def has_delete_without_where(command: str) -> bool:
    statements = [part.strip() for part in command.split(";") if part.strip()]
    for statement in statements:
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE):
            if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
                return True
    return False


def block_reason(command: str) -> str | None:
    normalized = " ".join(command.strip().split())
    lowered = normalized.lower()
    words = shell_words(lowered)

    if re.search(r"\brm\s+-[^\s]*r[^\s]*f|rm\s+-[^\s]*f[^\s]*r", lowered):
        return "rm -rf recursively and forcibly removes files"
    if re.search(r"\bdrop\s+table\b", lowered):
        return "DROP TABLE can destroy database schema and data"
    if re.search(r"\btruncate\b", lowered):
        return "TRUNCATE can irreversibly remove table data"
    if "git" in words and "push" in words and (
        "--force" in words or "-f" in words or "--force-with-lease" in words
    ):
        return "force-pushing can rewrite shared Git history"
    if has_delete_without_where(normalized):
        return "DELETE FROM without WHERE can remove every row"
    return None


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    command = payload.get("command")
    if isinstance(command, str):
        return command

    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_blocked(command: str, path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with BLOCKED_LOG.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\t{path}\t{reason}\t{command}\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked destructive Bash command: " + reason
                ),
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive_bash_guard: invalid hook payload: {exc}", file=sys.stderr)
        return 0

    command = extract_command(payload)
    reason = block_reason(command)
    if not reason:
        return 0

    log_blocked(command, project_path(payload), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
