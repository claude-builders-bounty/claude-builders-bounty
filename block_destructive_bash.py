#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin. If the event is a Bash tool call with a
command matching destructive patterns, logs the attempt and returns a Claude Code
permissionDecision=deny response. Safe commands exit 0 with no output.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Tuple

DANGEROUS_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf / rm -fr style recursive force deletion",
        re.compile(r"(?:^|[;&|()\n])\s*rm\s+-[^\n;&|]*[rR][^\n;&|]*[fF]|(?:^|[;&|()\n])\s*rm\s+-[^\n;&|]*[fF][^\n;&|]*[rR]"),
    ),
    ("DROP TABLE statement", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("TRUNCATE statement", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    (
        "git push --force / -f",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?\b|\s-f\b)", re.IGNORECASE),
    ),
)

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def iter_sql_statements(command: str) -> Iterable[str]:
    """Split enough for the DELETE-without-WHERE safety check.

    This intentionally favors safety over SQL completeness. It catches common
    inline shell SQL such as psql -c "DELETE FROM users" and sqlite3 db
    'DELETE FROM sessions;'.
    """
    for part in re.split(r"[;\n]", command):
        stripped = part.strip()
        if stripped:
            yield stripped


def dangerous_reason(command: str) -> str | None:
    for label, pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return label

    for statement in iter_sql_statements(command):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "DELETE FROM without WHERE clause"
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    log_dir = Path(os.environ.get("HOME", str(Path.home()))) / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project = project_path.replace("\n", " ")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp}\tproject={safe_project}\treason={reason}\tcommand={safe_command}\n")


def deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason}. Review the command and choose a safer, reversible action."
            ),
        }
    }
    print(json.dumps(response, separators=(",", ":")))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed hook input should not break normal Claude Code usage.
        return 0

    if payload.get("hook_event_name") not in (None, "PreToolUse"):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = dangerous_reason(command)
    if reason is None:
        return 0

    project_path = (
        payload.get("cwd")
        or payload.get("project_dir")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_block(command, str(project_path), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
