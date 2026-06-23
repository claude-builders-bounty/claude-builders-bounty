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


BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive force removal", re.compile(r"(^|[;&|]\s*)rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-.[A-Za-z]*f[A-Za-z]*r)\b")),
    ("table drop", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b")),
    ("truncate statement", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("delete statement without WHERE", re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.IGNORECASE)),
)


def load_event(stdin: str) -> dict[str, Any]:
    try:
        value = json.loads(stdin or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def extract_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def find_block_reason(command: str) -> str | None:
    for label, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return label
    return None


def append_log(command: str, reason: str, project_path: str | None) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "project_path": project_path or os.getcwd(),
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def decision(reason: str) -> dict[str, Any]:
    message = (
        f"Blocked destructive Bash command ({reason}). "
        "Choose a non-destructive command or ask the user before retrying."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }


def main() -> int:
    event = load_event(sys.stdin.read())
    if event.get("tool_name") != "Bash":
        return 0

    command = extract_command(event)
    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = event.get("cwd") if isinstance(event.get("cwd"), str) else None
    append_log(command, reason, project_path)
    print(json.dumps(decision(reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
