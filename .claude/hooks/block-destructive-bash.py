#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin and denies Bash commands matching
known destructive patterns. Blocked attempts are appended to
~/.claude/hooks/blocked.log with timestamp, attempted command, and project path.
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

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _strip_sql_comments(sql: str) -> str:
    """Remove common SQL comments before checking for WHERE clauses."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n\r]*", " ", sql)
    sql = re.sub(r"#[^\n\r]*", " ", sql)
    return sql


def _has_dangerous_delete_without_where(command: str) -> bool:
    """Return True when any DELETE FROM statement lacks a WHERE before its end.

    Statement end is approximated by semicolon or end-of-string. This catches
    `DELETE FROM users` and `DELETE FROM users;` while allowing
    `DELETE FROM users WHERE id = 1`.
    """
    sql = _strip_sql_comments(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        tail = sql[match.end():]
        statement = tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def _first_shell_word(command: str) -> str:
    try:
        words = shlex.split(command, comments=False, posix=True)
    except ValueError:
        return ""
    return Path(words[0]).name if words else ""


def _is_plain_text_search(command: str) -> bool:
    """Avoid blocking harmless searches for dangerous-looking text."""
    return _first_shell_word(command) in {"grep", "rg", "ag"}


def dangerous_reason(command: str) -> str | None:
    """Return a human-readable block reason, or None when command is allowed."""
    if _is_plain_text_search(command):
        return None
    checks: list[tuple[re.Pattern[str], str]] = [
        (
            re.compile(r"(?:^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b"),
            "rm -rf can recursively and forcefully delete files",
        ),
        (
            re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
            "DROP TABLE can permanently remove database tables",
        ),
        (
            re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:$|[\s;|&]|=)", re.IGNORECASE),
            "git push --force can overwrite remote history",
        ),
        (
            re.compile(r"\btruncate\b", re.IGNORECASE),
            "TRUNCATE can erase table contents",
        ),
    ]
    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    if _has_dangerous_delete_without_where(command):
        return "DELETE FROM without a WHERE clause can erase all rows"

    return None


def project_path(payload: dict[str, Any]) -> str:
    """Extract the best available project path from Claude Code hook input."""
    candidates = [
        payload.get("cwd"),
        payload.get("project_dir"),
        payload.get("project_path"),
        payload.get("workspace"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.getcwd(),
    ]
    return next((str(value) for value in candidates if value), "unknown")


def log_block(command: str, project: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked destructive Bash command: {reason}.",
                }
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON input: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = dangerous_reason(command)
    if not reason:
        return 0

    log_block(command, project_path(payload), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
