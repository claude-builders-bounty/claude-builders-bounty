#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code's JSON hook payload from stdin. When a dangerous
Bash command is detected, it writes a blocked-attempt record to
~/.claude/hooks/blocked.log and emits a PreToolUse permission denial.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf",
        re.compile(
            r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])(?:\s|$)"
        ),
    ),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b", re.IGNORECASE),
    ),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b|;).)*(?:;|$)", re.IGNORECASE | re.DOTALL),
    ),
)


def extract_command(payload: dict[str, Any]) -> str:
    """Extract a Bash command string from a Claude Code hook payload."""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    """Return True if the payload is for Claude Code's Bash tool."""
    tool_name = payload.get("tool_name") or payload.get("toolName")
    return str(tool_name or "Bash").lower() == "bash"


def find_block_reason(command: str) -> str | None:
    """Return the first matching blocked pattern description, if any."""
    for reason, pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> Path:
    """Append timestamp, command, and project path to blocked.log."""
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    sanitized_command = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{sanitized_command}\t{project_path}\t{reason}\n")
    return log_path


def deny(reason: str) -> None:
    """Emit Claude Code's JSON permission denial response."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked destructive Bash command ({reason}). "
                        "Use a safer command or ask the user for explicit approval."
                    ),
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block_destructive_commands.py: invalid JSON input: {exc}", file=sys.stderr)
        return 0

    if not isinstance(payload, dict) or not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())
    log_blocked_attempt(command, project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
