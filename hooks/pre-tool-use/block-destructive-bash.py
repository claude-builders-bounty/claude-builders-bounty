#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_PATH = HOOK_DIR / "blocked.log"


BLOCK_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|]\s*)rm\s+(?:-[^\s]*[rR][^\s]*[fF]|-[^\s]*[fF][^\s]*[rR])(?:\s|$)"),
        "Recursive force deletion can irreversibly remove project or system files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE destroys database schema and data.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE removes all rows from a table.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;|&]*(?:--force(?:-with-lease)?|-f)\b", re.IGNORECASE),
        "Force pushing can overwrite remote history.",
    ),
]

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    for key in ("command", "cmd", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd")
        if isinstance(value, str) and value:
            return value

    return os.getcwd()


def find_block_reason(command: str) -> tuple[str, str] | None:
    for label, pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return label, reason

    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return (
            "DELETE FROM without WHERE",
            "DELETE FROM without a WHERE clause can remove every row in a table.",
        )

    return None


def append_block_log(command: str, project: str, label: str) -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "blocked_pattern": label,
        "project_path": project,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def allow_response() -> dict[str, Any]:
    return {
        "decision": "allow",
        "hookSpecificOutput": {"permissionDecision": "allow"},
    }


def block_response(command: str, label: str, reason: str) -> dict[str, Any]:
    return {
        "decision": "block",
        "reason": (
            f"Blocked dangerous bash command pattern `{label}`. {reason} "
            f"The attempted command was logged to {LOG_PATH}."
        ),
        "hookSpecificOutput": {
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked dangerous bash command pattern `{label}`. {reason} "
                f"The attempted command was logged to {LOG_PATH}."
            ),
        },
        "attempted_command": command,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"decision": "block", "reason": f"Invalid hook payload JSON: {exc}"}))
        return 1

    command = extract_command(payload)
    if not command:
        print(json.dumps(allow_response()))
        return 0

    block = find_block_reason(command)
    if block is None:
        print(json.dumps(allow_response()))
        return 0

    label, reason = block
    append_block_log(command, project_path(payload), label)
    print(json.dumps(block_response(command, label, reason)))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
