#!/usr/bin/env python3
"""Deny destructive Bash commands before Claude Code executes them.

The hook reads the JSON payload that Claude Code sends to a ``PreToolUse``
command hook on stdin.  It stays silent for commands that are not Bash or do
not match a destructive pattern, allowing the normal permission flow to run.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


_RM_RF = re.compile(r"\brm\s+-rf(?:\s|$)", re.IGNORECASE)
_DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
_TRUNCATE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
_GIT_FORCE_PUSH = re.compile(
    r"\bgit\s+push\b[^;\n|&]*\s--force(?:\s|$)", re.IGNORECASE
)
_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
_WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _delete_without_where(command: str) -> bool:
    """Return whether a DELETE statement lacks a WHERE clause."""

    for match in _DELETE_FROM.finditer(command):
        # Inspect one shell/SQL statement at a time so a later command such as
        # ``echo WHERE`` cannot make an earlier DELETE look safe.
        statement = re.split(r"[;\n]", command[match.end() :], maxsplit=1)[0]
        if not _WHERE.search(statement):
            return True
    return False


def blocking_reason(command: str) -> str | None:
    """Return a human-readable reason, or ``None`` for a safe command."""

    if _RM_RF.search(command):
        return "rm -rf can recursively delete files"
    if _GIT_FORCE_PUSH.search(command):
        return "git push --force can overwrite remote history"
    if _DROP_TABLE.search(command):
        return "DROP TABLE can destroy a database table"
    if _TRUNCATE.search(command):
        return "TRUNCATE can remove all rows from a table"
    if _delete_without_where(command):
        return "DELETE FROM without WHERE can remove every row"
    return None


def _payload() -> dict[str, Any] | None:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def _command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    value = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR")
    return str(value or os.getcwd())


def _write_log(command: str, project_path: str, reason: str) -> None:
    # The override keeps the hook easy to test without changing the production
    # default of ``~/.claude/hooks/blocked.log``.
    home = Path(os.environ.get("CLAUDE_HOOK_HOME", str(Path.home())))
    log_path = home / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    payload = _payload()
    if payload is None or payload.get("tool_name") not in (None, "Bash"):
        return 0

    command = _command(payload)
    reason = blocking_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _write_log(command, project_path, reason)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Destructive command blocked: {reason}. "
                        "Review it and use a safer, scoped alternative."
                    ),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
