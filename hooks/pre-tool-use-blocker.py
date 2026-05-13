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


BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"(^|[;&|()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])(?:\s|$)"),
        "Recursive force removal can delete large parts of the project or filesystem.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE permanently removes database tables.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--(?:force|force-with-lease)\b", re.IGNORECASE),
        "Force pushing can overwrite shared branch history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE removes all rows from a table.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.IGNORECASE),
        "DELETE FROM without a WHERE clause can remove every row in a table.",
    ),
)


def main() -> int:
    payload = read_payload()

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    cwd = str(payload.get("cwd") or os.getcwd())
    blocked = find_blocked_rule(command)

    if blocked is None:
        return 0

    pattern_name, reason = blocked
    log_error = write_block_log(
        command=command,
        cwd=cwd,
        pattern_name=pattern_name,
    )
    deny(reason=reason, pattern_name=pattern_name, cwd=cwd, log_error=log_error)
    return 0


def read_payload() -> dict[str, Any]:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return {}

    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


def find_blocked_rule(command: str) -> tuple[str, str] | None:
    for pattern_name, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return pattern_name, reason
    return None


def write_block_log(*, command: str, cwd: str, pattern_name: str) -> str | None:
    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "pattern": pattern_name,
            "command": command,
            "project_path": cwd,
        }

        with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as error:
        return str(error)

    return None


def deny(
    *,
    reason: str,
    pattern_name: str,
    cwd: str,
    log_error: str | None = None,
) -> None:
    message = (
        f"Blocked destructive Bash command ({pattern_name}). {reason} "
        f"Project path: {cwd}. Review the command and ask the user for an "
        "explicit safer alternative before continuing."
    )
    if log_error:
        message += f" The command was blocked, but logging failed: {log_error}."

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    raise SystemExit(main())
