#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _compact(command: str) -> str:
    return " ".join(command.split())


def extract_command(payload: dict) -> str:
    """Return the bash command from common Claude Code hook payload shapes."""
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


def delete_without_where(command: str) -> bool:
    """Match DELETE FROM statements that do not contain WHERE before statement end."""
    for match in re.finditer(r"\bDELETE\s+FROM\b", command, flags=re.IGNORECASE):
        rest = command[match.end() :]
        statement = re.split(r"[;\n]", rest, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    checks: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\brm\s+(?:[^\n;&|]*\s)?-[^\n;&|]*r[^\n;&|]*f", re.IGNORECASE), "rm -rf removes files recursively and forcefully"),
        (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE can destroy database schema/data"),
        (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE can delete table contents"),
        (re.compile(r"\bgit\s+push\b[^\n;&|]*--force(?:-with-lease)?\b", re.IGNORECASE), "force-pushing can rewrite shared history"),
    ]
    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    if delete_without_where(command):
        return "DELETE FROM without WHERE can delete every row"

    return None


def log_block(command: str, reason: str, payload: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    project_path = payload.get("cwd") or payload.get("project_path") or os.getcwd()
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={_compact(command)}\n"
        )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Invalid hook payload: stay out of the way.
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if not reason:
        return 0

    log_block(command, reason, payload)
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": f"Blocked destructive bash command: {reason}. Review the command and use a safer, explicit alternative.",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
