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


LOG_PATH = Path(os.environ.get("CLAUDE_BLOCKED_LOG", "~/.claude/hooks/blocked.log")).expanduser()


BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"\brm\b(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)", re.IGNORECASE),
        "Recursive forced removal is blocked.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE is blocked.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(--force|-f\b)", re.IGNORECASE),
        "Forced git push is blocked.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE is blocked.",
    ),
)


DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def load_hook_input() -> dict[str, Any]:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def get_bash_command(hook_input: dict[str, Any]) -> str:
    if hook_input.get("tool_name") != "Bash":
        return ""

    tool_input = hook_input.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def find_block_reason(command: str) -> str | None:
    for label, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return f"{reason} Matched pattern: {label}."

    if has_delete_without_where(command):
        return "DELETE FROM without a WHERE clause is blocked."

    return None


def has_delete_without_where(command: str) -> bool:
    statements = re.split(r";|&&|\|\|", command)
    for statement in statements:
        match = DELETE_FROM_RE.search(statement)
        if match and not WHERE_RE.search(statement[match.end() :]):
            return True
    return False


def write_block_log(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload))


def main() -> int:
    hook_input = load_hook_input()
    command = get_bash_command(hook_input)
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    cwd = hook_input.get("cwd")
    write_block_log(command, cwd if isinstance(cwd, str) else "", reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
