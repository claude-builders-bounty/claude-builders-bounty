#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Install this file under ~/.claude/hooks/destructive-command-guard.py and wire it
as a PreToolUse hook for Bash in ~/.claude/settings.json.

Claude Code blocks a PreToolUse hook when the hook exits with status 2.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCK_EXIT_CODE = 2
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _read_payload() -> dict[str, Any]:
    """Read Claude hook JSON from stdin or CLAUDE_TOOL_INPUT fallback."""
    raw = sys.stdin.read().strip()
    if not raw:
        raw = os.environ.get("CLAUDE_TOOL_INPUT", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {"raw": raw}


def _extract_command(payload: dict[str, Any]) -> str:
    """Extract a Bash command from common Claude Code hook payload shapes."""
    candidates: list[Any] = [
        payload.get("command"),
        payload.get("tool_input", {}).get("command") if isinstance(payload.get("tool_input"), dict) else None,
        payload.get("input", {}).get("command") if isinstance(payload.get("input"), dict) else None,
        payload.get("parameters", {}).get("command") if isinstance(payload.get("parameters"), dict) else None,
        payload.get("raw"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _project_path(payload: dict[str, Any]) -> str:
    """Find the project path for blocked-command audit logs."""
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    value = os.environ.get("CLAUDE_PROJECT_DIR")
    if value:
        return value
    return os.getcwd()


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def _delete_without_where(command: str) -> bool:
    """Detect DELETE FROM statements that do not include WHERE before statement end."""
    normalized = _strip_sql_comments(command)
    for match in re.finditer(r"\bDELETE\s+FROM\b", normalized, flags=re.IGNORECASE):
        tail = normalized[match.end() :]
        statement = re.split(r";|\n", tail, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    """Return a human-readable block reason, or None when command is allowed."""
    compact = " ".join(command.split())

    if re.search(
        r"(^|[;|\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|-[A-Za-z]*r[A-Za-z]*\s+-[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*\s+-[A-Za-z]*r[A-Za-z]*)",
        compact,
    ):
        return "rm -rf style recursive force deletion is blocked"

    if re.search(r"\bDROP\s+TABLE\b", compact, flags=re.IGNORECASE):
        return "DROP TABLE is blocked"

    if re.search(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=|-with-lease)", compact):
        return "git push --force is blocked"

    if re.search(r"\bTRUNCATE\b", compact, flags=re.IGNORECASE):
        return "TRUNCATE is blocked"

    if _delete_without_where(command):
        return "DELETE FROM without a WHERE clause is blocked"

    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    payload = _read_payload()
    command = _extract_command(payload)

    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)

    print(
        "Blocked dangerous Bash command before execution.\n"
        f"Reason: {reason}.\n"
        f"Project: {project_path}.\n"
        f"Command: {command}\n\n"
        "Choose a safer, narrower command. If this is intentional, ask the user "
        "for explicit confirmation and use a non-destructive alternative when possible.",
        file=sys.stderr,
    )
    return BLOCK_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
