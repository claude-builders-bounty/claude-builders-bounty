#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _normalise(command: str) -> str:
    return " ".join(command.strip().split())


def _block_log_path() -> Path:
    override = os.environ.get("CLAUDE_HOOK_BLOCK_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def _delete_without_where(command: str) -> bool:
    statements = re.split(r";|\n", command, flags=re.IGNORECASE)
    for statement in statements:
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE):
            if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
                return True
    return False


def get_block_reason(command: str) -> str | None:
    """Return the reason a command should be blocked, or None if it is allowed."""
    normalized = _normalise(command)

    destructive_patterns: list[tuple[str, str]] = [
        (
            r"(?:^|[;&|]\s*)(?:sudo\s+)?(?:command\s+)?rm\s+(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)",
            "rm -rf style removal can recursively delete files without recovery.",
        ),
        (
            r"\bdrop\s+table\b",
            "DROP TABLE can destroy database schema and data.",
        ),
        (
            r"\btruncate(?:\s+table)?\b",
            "TRUNCATE can erase table contents without row-by-row safeguards.",
        ),
        (
            r"\bgit\s+push\b(?=[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b)",
            "Force pushing can rewrite shared Git history.",
        ),
    ]

    for pattern, reason in destructive_patterns:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return reason

    if _delete_without_where(normalized):
        return "DELETE FROM without a WHERE clause can remove every row in a table."

    return None


def _load_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "workspace_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project_dir:
        return env_project_dir

    return os.getcwd()


def _log_block(command: str, project_path: str, reason: str) -> None:
    block_log = _block_log_path()
    block_log.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with block_log.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason} Use a safer command or ask the user for explicit approval."
            ),
        }
    }
    print(json.dumps(response))


def main() -> int:
    payload = _load_input()
    if payload.get("tool_name") != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = get_block_reason(command)
    if reason is None:
        return 0

    _log_block(command, _project_path(payload), reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
