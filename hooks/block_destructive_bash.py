#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_REASONS = {
    "rm_rf": "rm -rf style recursive force deletion is blocked.",
    "drop_table": "DROP TABLE is blocked because it can destroy schema data.",
    "truncate": "TRUNCATE is blocked because it can delete table data.",
    "git_force_push": "git push --force style history rewrites are blocked.",
    "delete_without_where": "DELETE FROM without a WHERE clause is blocked.",
}


def normalize_sql(sql: str) -> str:
    sql = re.sub(r"--[^\n\r]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"\s+", " ", sql).strip()


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def has_rm_rf(command: str) -> bool:
    words = shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue

        saw_recursive = False
        saw_force = False
        for option in words[index + 1 :]:
            if option == "--":
                break
            if not option.startswith("-"):
                break
            if option in ("-r", "-R", "--recursive"):
                saw_recursive = True
            if option in ("-f", "--force"):
                saw_force = True
            if option.startswith("-") and not option.startswith("--"):
                saw_recursive = saw_recursive or "r" in option.lower()
                saw_force = saw_force or "f" in option.lower()
            if saw_recursive and saw_force:
                return True
    return False


def has_git_force_push(command: str) -> bool:
    words = shell_words(command)
    for index in range(len(words) - 2):
        if words[index : index + 2] != ["git", "push"]:
            continue
        push_args = words[index + 2 :]
        return any(
            arg in ("--force", "-f", "--force-with-lease")
            or arg.startswith("--force=")
            or arg.startswith("--force-with-lease=")
            for arg in push_args
        )
    return False


def has_delete_without_where(command: str) -> bool:
    sql = normalize_sql(command).lower()
    statements = [part.strip() for part in sql.split(";") if part.strip()]
    for statement in statements:
        if re.search(r"\bdelete\s+from\b", statement) and not re.search(r"\bwhere\b", statement):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    sql = normalize_sql(command)
    if has_rm_rf(command):
        return BLOCK_REASONS["rm_rf"]
    if has_git_force_push(command):
        return BLOCK_REASONS["git_force_push"]
    if re.search(r"\bdrop\s+table\b", sql, flags=re.IGNORECASE):
        return BLOCK_REASONS["drop_table"]
    if re.search(r"\btruncate\b", sql, flags=re.IGNORECASE):
        return BLOCK_REASONS["truncate"]
    if has_delete_without_where(command):
        return BLOCK_REASONS["delete_without_where"]
    return None


def log_path() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_BLOCKED_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(payload: dict[str, Any], command: str, reason: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": payload.get("cwd", ""),
        "attempted_command": command,
        "reason": reason,
        "tool_name": payload.get("tool_name", ""),
        "tool_use_id": payload.get("tool_use_id", ""),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    log_blocked_attempt(payload, command, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
