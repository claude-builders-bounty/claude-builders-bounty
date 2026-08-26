#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOK_DIR / "blocked.log"


def _delete_without_where(command: str) -> bool:
    """Return True when any DELETE FROM statement has no WHERE before ';' or EOL."""
    for match in re.finditer(r"\bDELETE\s+FROM\b", command, flags=re.IGNORECASE):
        tail = command[match.end() :]
        statement = re.split(r"[;\n]", tail, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
            return True
    return False


def _rm_recursive_force(command: str) -> bool:
    """Detect rm invocations that combine recursive and force flags."""
    for match in re.finditer(r"\brm\b([^;&|\n]*)", command, flags=re.IGNORECASE):
        args = match.group(1).split()
        recursive = False
        force = False
        for arg in args:
            if not arg.startswith("-"):
                continue
            if arg == "--recursive":
                recursive = True
            elif arg == "--force":
                force = True
            elif not arg.startswith("--"):
                flags = arg[1:]
                recursive = recursive or ("r" in flags or "R" in flags)
                force = force or ("f" in flags)
        if recursive and force:
            return True
    return False


def blocked_reason(command: str) -> str | None:
    """Return a human-readable reason when *command* must be blocked."""
    if _rm_recursive_force(command):
        return "recursive forced deletion (rm -rf / equivalent)"

    checks: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "SQL DROP TABLE"),
        (
            re.compile(r"\bgit\s+push\b[^;&|\n]*(?:--force(?:-with-lease|-if-includes)?|-f)(?:\s|$)", re.IGNORECASE),
            "forced git push",
        ),
        (re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE), "SQL TRUNCATE"),
    ]

    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    if _delete_without_where(command):
        return "DELETE FROM without a WHERE clause"

    return None


def log_block(input_data: dict[str, Any], command: str, reason: str) -> None:
    """Append a JSONL audit record for every blocked attempt."""
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    project_path = input_data.get("cwd") or os.getcwd()
    record = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError) as exc:
        print(f"Hook input is not valid JSON: {exc}", file=sys.stderr)
        return 1

    if input_data.get("tool_name") != "Bash":
        return 0

    tool_input = input_data.get("tool_input") or {}
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    log_block(input_data, command, reason)
    message = (
        f"BLOCKED destructive Bash command: {reason}. "
        "Choose a non-destructive alternative or ask the user for an explicitly safer operation."
    )

    # Claude Code treats exit code 2 from PreToolUse as a blocking decision and
    # feeds stderr back to Claude. The structured object mirrors the current
    # PreToolUse hook output format as well.
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                },
                "systemMessage": message,
            }
        )
    )
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
