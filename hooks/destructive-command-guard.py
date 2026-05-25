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

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "recursive force delete",
        re.compile(r"(^|[;&|`$()\n])\s*rm\s+[^\n;&|]*-[^\n;&|]*r[^\n;&|]*f|(^|[;&|`$()\n])\s*rm\s+[^\n;&|]*-[^\n;&|]*f[^\n;&|]*r", re.IGNORECASE),
        "rm -rf can irreversibly delete files. Ask the user before running destructive deletes.",
    ),
    (
        "drop table",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE can destroy database schema/data. Require explicit human approval.",
    ),
    (
        "force push",
        re.compile(
            r"\bgit\s+push\b(?=[^\n;&|]*\s(?:--force|-f|--force-with-lease)(?:\s|$))",
            re.IGNORECASE,
        ),
        "Force-pushing can rewrite shared history. Require explicit human approval.",
    ),
    (
        "truncate",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE can delete all rows from a table. Require explicit human approval.",
    ),
    (
        "delete without where",
        re.compile(r"\bDELETE\s+FROM\s+[\w.\"`]+(?![^;\n]*\bWHERE\b)", re.IGNORECASE),
        "DELETE FROM without a WHERE clause can remove every row. Add a WHERE clause or ask the user.",
    ),
]


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {"raw_input": raw}


def find_command(value: Any) -> str:
    """Find the bash command across common Claude Code hook payload shapes."""
    if isinstance(value, dict):
        for key in ("command", "cmd", "bash_command", "input"):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item
        for key in ("tool_input", "toolUse", "tool_use", "parameters", "args"):
            command = find_command(value.get(key))
            if command:
                return command
        for item in value.values():
            command = find_command(item)
            if command:
                return command
    elif isinstance(value, list):
        for item in value:
            command = find_command(item)
            if command:
                return command
    elif isinstance(value, str):
        return value
    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "root", "repo_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    for _name, pattern, message in BLOCK_RULES:
        if pattern.search(command):
            return message
    return None


def log_block(command: str, path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": path,
        "attempted_command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = load_payload()
    command = find_command(payload)
    reason = blocked_reason(command)
    if not reason:
        return 0

    path = project_path(payload)
    log_block(command, path, reason)
    print(
        "Blocked by destructive-command-guard: "
        f"{reason}\nCommand: {command}\nProject: {path}",
        file=sys.stderr,
    )
    # Claude Code treats a non-zero pre-tool-use hook as a blocked tool call.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
