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


SQL_BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE can permanently remove database tables.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE can permanently remove table contents.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b|;|\n).)*?(?:;|$)", re.IGNORECASE | re.DOTALL),
        "DELETE FROM without a WHERE clause can remove every row in a table.",
    ),
)

SHELL_BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "recursive forced removal",
        re.compile(
            r"(^|[;&|]\s*)rm\s+"
            r"(?=[^\n;&|]*(?:-[A-Za-z]*[rR][A-Za-z]*|--recursive)(?:\s|=|$))"
            r"(?=[^\n;&|]*(?:-[A-Za-z]*[fF][A-Za-z]*|--force)(?:\s|=|$))",
            re.IGNORECASE,
        ),
        "rm -rf style commands can permanently delete large parts of the workspace.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b", re.IGNORECASE),
        "git push --force can overwrite remote history.",
    ),
)


def _read_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        return {"hook_event_name": "PreToolUse", "_parse_error": str(exc)}


def _bash_command(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _find_block_reason(command: str) -> str | None:
    for name, pattern, reason in SHELL_BLOCK_RULES + SQL_BLOCK_RULES:
        if pattern.search(command):
            return f"Blocked destructive command ({name}): {reason}"
    return None


def _log_block(payload: dict[str, Any], command: str, reason: str) -> str | None:
    log_dir = Path.home() / ".claude" / "hooks"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        project_path = payload.get("cwd") or os.getcwd()
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "project_path": str(project_path),
            "command": command,
            "reason": reason,
        }
        with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError as exc:
        return f"Unable to write blocked command log: {exc}"
    return None


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    payload = _read_payload()
    command = _bash_command(payload)

    if not command:
        print(json.dumps({"continue": True}))
        return 0

    reason = _find_block_reason(command)
    if reason is None:
        print(json.dumps({"continue": True}))
        return 0

    log_error = _log_block(payload, command, reason)
    if log_error:
        print(log_error, file=sys.stderr)
    print(json.dumps(_deny(reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
