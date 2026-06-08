#!/usr/bin/env python3
"""Block destructive Bash commands before Claude Code runs them."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_PATTERNS = [
    ("rm -rf", re.compile(r"(^|[;&|`$()\s])rm\s+[^\n;]*-(?:[^\n;\s]*r[^\n;\s]*f|[^\n;\s]*f[^\n;\s]*r)(?:\s|$)")),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:\s|=|$)")),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b).)*(?:;|$)", re.IGNORECASE | re.DOTALL)),
]


def extract_command(payload: dict[str, Any]) -> str:
    """Claude changes shapes; look in the common places first."""
    tool_input = payload.get("tool_input")
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


def first_block_reason(command: str) -> str | None:
    for label, pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return label
    return None


def write_block_log(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    clean_command = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{project_path}\t{reason}\t{clean_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Could not parse Claude Code hook input: {error}", file=sys.stderr)
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = first_block_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())
    write_block_log(command, project_path, reason)
    print(
        f"Blocked destructive Bash command ({reason}). "
        "Review the command and use a safer, explicit alternative.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
