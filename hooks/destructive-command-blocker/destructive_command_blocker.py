#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

Reads a Claude Code hook payload from stdin and exits non-zero when a Bash tool
command matches a destructive pattern. Blocked attempts are appended to
~/.claude/hooks/blocked.log with timestamp, command, and project path.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"(^|[;&|`$()\s])rm\s+[^\n;|&]*-(?:[^\n;|&\s]*r[^\n;|&\s]*f|[^\n;|&\s]*f[^\n;|&\s]*r)\b", re.IGNORECASE),
        "Recursive force deletion with rm -rf can destroy project or system files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE permanently removes database tables.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;|&]*(?:--force\b|-f\b|--force-with-lease\b)", re.IGNORECASE),
        "Forced git pushes can rewrite shared history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE removes table contents without row-level safeguards.",
    ),
)

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some local tests or wrappers may pass the command as raw stdin.
        return {"tool_name": "Bash", "tool_input": {"command": raw}}


def extract_command(payload: dict[str, Any]) -> str | None:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    tool_input = payload.get("tool_input") or payload.get("input") or {}

    if isinstance(tool_input, str):
        command = tool_input
    elif isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script")
    else:
        command = None

    if command is None:
        return None

    # Only block Bash/shell commands; never interfere with other tool calls.
    if tool_name and tool_name.lower() not in {"bash", "shell", "terminal"}:
        return None

    return str(command)


def split_sql_statements(command: str) -> list[str]:
    # Good enough for safety screening: split common command/SQL separators.
    return [part.strip() for part in re.split(r"[;\n]", command) if part.strip()]


def find_block_reason(command: str) -> tuple[str, str] | None:
    normalized = command.strip()

    for label, pattern, reason in BLOCK_RULES:
        if pattern.search(normalized):
            return label, reason

    for statement in split_sql_statements(normalized):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can remove every row in a table."

    return None


def project_path(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("workspace"),
        payload.get("tool_input", {}).get("cwd") if isinstance(payload.get("tool_input"), dict) else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    return os.getcwd()


def log_blocked(command: str, project: str, label: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{project}\t{label}\t{safe_command}\n")


def main() -> int:
    payload = load_payload()
    command = extract_command(payload)
    if command is None:
        return 0

    match = find_block_reason(command)
    if match is None:
        return 0

    label, reason = match
    project = project_path(payload)
    log_blocked(command, project, label)

    print(
        "Blocked destructive Bash command.\n"
        f"Pattern: {label}\n"
        f"Reason: {reason}\n"
        "Revise the command to use a safer, scoped operation before retrying.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
