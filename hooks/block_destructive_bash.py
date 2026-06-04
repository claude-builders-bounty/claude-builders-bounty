#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the Claude Code hook JSON event from stdin. If the event is a Bash tool
call with a dangerous command, writes a PreToolUse denial decision to stdout and
logs the blocked attempt to ~/.claude/hooks/blocked.log.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


DANGEROUS_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-\w*f\w*r)\b"),
        "Recursive forced removal can delete large parts of the filesystem.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE permanently removes database tables.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b", re.IGNORECASE),
        "Force-pushing can overwrite remote branch history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE can irreversibly delete all rows from a table.",
    ),
]

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\s+[\w.\"`\[\]-]+(?P<tail>[^;]*)", re.IGNORECASE | re.DOTALL)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _read_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Invalid hook input should not break normal Claude Code execution.
        return {}
    return data if isinstance(data, dict) else {}


def _extract_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def _project_path(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "workspace", "workspace_dir"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _match_delete_without_where(command: str) -> tuple[str, str] | None:
    for match in DELETE_FROM_RE.finditer(command):
        tail = match.group("tail") or ""
        if not WHERE_RE.search(tail):
            return (
                "DELETE FROM without WHERE",
                "DELETE FROM without a WHERE clause can remove every row in a table.",
            )
    return None


def find_block_reason(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return name, reason
    return _match_delete_without_where(command)


def _log_blocked(command: str, project_path: str, pattern_name: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    one_line_command = " ".join(command.split())
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp}\tproject={project_path}\tpattern={pattern_name}\tcommand={one_line_command}\n"
        )


def _deny(pattern_name: str, reason: str) -> None:
    message = (
        f"Blocked destructive Bash command ({pattern_name}). {reason} "
        "Ask the user for explicit confirmation or use a safer, scoped command."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def main() -> int:
    event = _read_event()
    if event.get("tool_name") != "Bash":
        return 0

    command = _extract_command(event)
    if not command:
        return 0

    match = find_block_reason(command)
    if not match:
        return 0

    pattern_name, reason = match
    _log_blocked(command, _project_path(event), pattern_name)
    _deny(pattern_name, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
