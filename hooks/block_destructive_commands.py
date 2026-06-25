#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive bash commands.

The hook reads the Claude Code hook payload from stdin and exits with status 2
when a risky command is detected. Claude Code shows stderr to Claude when a
PreToolUse hook exits with status 2.
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


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_command(payload: dict[str, Any]) -> str:
    """Return the bash command from common Claude Code hook payload shapes."""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "input"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    for key in ("command", "cmd", "input"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def _delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement_tail = command[match.end() :]
        statement = re.split(r"[;\n]", statement_tail, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    normalized = _normalize_space(command)
    checks = (
        (
            r"\brm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\b",
            "rm -rf can recursively delete files without confirmation",
        ),
        (r"\bdrop\s+table\b", "DROP TABLE can permanently remove database tables"),
        (r"\bgit\s+push\b[^\n;]*\s--force(?:\b|=)", "git push --force can overwrite remote history"),
        (r"\btruncate\b", "TRUNCATE can permanently remove table data"),
    )

    for pattern, reason in checks:
        if re.search(pattern, normalized, re.IGNORECASE):
            return reason

    if _delete_without_where(normalized):
        return "DELETE FROM without a WHERE clause can remove every row in a table"

    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "command": command,
            "project_path": project_path,
            "reason": reason,
        },
        ensure_ascii=False,
    )
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block_destructive_commands: invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    if not isinstance(payload, dict):
        return 0

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name.lower() not in {"bash", "shell", "terminal"}:
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    log_blocked(command, project_path, reason)
    print(
        "Blocked destructive bash command before execution.\n"
        f"Reason: {reason}.\n"
        f"Attempted command: {command}\n"
        f"Project path: {project_path}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
