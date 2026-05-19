#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

Install by copying this file into ~/.claude/hooks/ and configuring it as a
pre-tool-use hook for Bash tool calls. The hook reads Claude Code hook JSON from
stdin and exits non-zero when a dangerous command is detected.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("rm -rf", re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-?[A-Za-z]*f[A-Za-z]*r)\b")),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=)", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b)[^;])*($|;)", re.IGNORECASE | re.DOTALL)),
]


def extract_command(payload: dict[str, Any]) -> str:
    """Return the bash command from common Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script")
        if isinstance(command, str):
            return command

    command = payload.get("command")
    if isinstance(command, str):
        return command

    return ""


def find_block_reason(command: str) -> str | None:
    for name, pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return name
    return None


def project_path(payload: dict[str, Any]) -> str:
    """Return a project path from hook payload metadata when available."""
    for key in ("cwd", "project_path", "workspace", "root"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    metadata = payload.get("metadata") or {}
    if isinstance(metadata, dict):
        for key in ("cwd", "project_path", "workspace", "root"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value

    return str(Path.cwd())


def log_block(command: str, reason: str, path: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    sanitized = command.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\treason={reason}\tproject_path={path}\tcommand={sanitized}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude Code hook JSON: {exc}", file=sys.stderr)
        return 2

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    command = extract_command(payload)

    if tool_name and tool_name.lower() != "bash":
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    path = project_path(payload)
    log_block(command, reason, path)
    print(f"Blocked dangerous bash command: {reason}. See ~/.claude/hooks/blocked.log for details.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
