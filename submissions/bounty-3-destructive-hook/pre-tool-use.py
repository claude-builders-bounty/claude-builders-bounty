#!/usr/bin/env python3
"""Claude Code PreToolUse hook — block destructive bash commands."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", re.I),
        "Recursive force delete (`rm -rf`) can cause irreversible data loss.",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.I),
        "`DROP TABLE` permanently deletes database tables.",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[A-Za-z_][\w]*\b", re.I),
        "`TRUNCATE` removes all rows from a table.",
    ),
    (
        re.compile(r"\bgit\s+push\b[^;\n]*(?:--force|-f)\b", re.I),
        "`git push --force` overwrites remote history.",
    ),
    (
        re.compile(r"\bDELETE\s+FROM\s+[A-Za-z_][\w]*\b", re.I),
        "`DELETE FROM` without a WHERE clause deletes every row.",
    ),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    legacy = payload.get("input") or {}
    if isinstance(legacy, dict):
        command = legacy.get("command")
        if isinstance(command, str):
            return command
    return ""


def is_delete_without_where(command: str) -> bool:
    if not re.search(r"\bDELETE\s+FROM\s+[A-Za-z_][\w]*\b", command, re.I):
        return False
    return not re.search(r"\bWHERE\b", command, re.I)


def match_reason(command: str) -> str | None:
    for pattern, reason in PATTERNS:
        if pattern.pattern.startswith(r"\bDELETE"):
            if is_delete_without_where(command):
                return reason
            continue
        if pattern.search(command):
            return reason
    return None


def log_block(command: str, project_path: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
    }
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = extract_command(payload).strip()
    if not command:
        sys.exit(0)

    reason = match_reason(command)
    if not reason:
        sys.exit(0)

    project_path = (
        payload.get("cwd")
        or payload.get("workspace")
        or payload.get("project_path")
        or str(Path.cwd())
    )
    log_block(command, project_path)

    message = (
        "COMMAND BLOCKED by destructive-command guard\n\n"
        f"Attempted: {command}\n\n"
        f"Reason: {reason}\n\n"
        f"Logged to: {LOG_FILE}\n\n"
        "Use a safer alternative (scoped paths, transactions, backups) or ask the user to run this manually."
    )
    print(message, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()