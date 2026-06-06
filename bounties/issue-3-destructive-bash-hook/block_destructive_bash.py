#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf / rm -fr",
        re.compile(r"(?<!\S)rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])(?:\s|$)"),
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b(?:(?![;&|]).)*(?:--force(?:-with-lease)?|-f)(?:\s|$)", re.IGNORECASE),
    ),
)

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _condense(command: str) -> str:
    return " ".join(command.replace("\\\n", " ").split())


def _delete_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        statement_tail = command[match.end() :]
        statement_tail = re.split(r"[;|&]", statement_tail, maxsplit=1)[0]
        if not WHERE_RE.search(statement_tail):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    normalized = _condense(command)

    for label, pattern in BLOCK_RULES:
        if pattern.search(normalized):
            return label

    if _delete_without_where(normalized):
        return "DELETE FROM without WHERE"

    return None


def get_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def get_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    env_path = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_path:
        return env_path

    return os.getcwd()


def get_log_path() -> Path:
    override = os.environ.get("CLAUDE_BLOCKED_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def write_block_log(command: str, project_path: str, reason: str) -> None:
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def deny_payload(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {reason}. Review the command and use a safer, scoped alternative.",
        }
    }


def handle(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("tool_name") != "Bash":
        return None

    command = get_command(payload)
    if not command:
        return None

    reason = find_block_reason(command)
    if reason is None:
        return None

    write_block_log(command, get_project_path(payload), reason)
    return deny_payload(reason)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        payload = {}

    decision = handle(payload)
    if decision is not None:
        print(json.dumps(decision, ensure_ascii=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
