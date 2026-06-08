#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


RM_RECURSIVE_FORCE_PATTERN = re.compile(
    r"(^|[;&|()\s])rm\s+"
    r"(?:(?:-[A-Za-z]*[rR][A-Za-z]*[fF][A-Za-z]*)|"
    r"(?:-[A-Za-z]*[fF][A-Za-z]*[rR][A-Za-z]*)|"
    r"(?:(?:--recursive|-r|-R)\s+(?:--force|-f))|"
    r"(?:(?:--force|-f)\s+(?:--recursive|-r|-R)))"
    r"(?=\s|$)",
)
DROP_TABLE_PATTERN = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_PATTERN = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_PATTERN = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_PATTERN = re.compile(r"\bwhere\b", re.IGNORECASE)


def find_block_reason(command: str) -> str | None:
    """Return the first destructive pattern reason, or None when allowed."""
    if RM_RECURSIVE_FORCE_PATTERN.search(command):
        return "rm recursive force command detected"

    if _has_git_force_push(command):
        return "git force push detected"

    if DROP_TABLE_PATTERN.search(command):
        return "DROP TABLE statement detected"

    if TRUNCATE_PATTERN.search(command):
        return "TRUNCATE statement detected"

    if _has_delete_from_without_where(command):
        return "DELETE FROM without WHERE clause detected"

    return None


def _has_git_force_push(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        tokens = command.split()

    lowered = [token.lower() for token in tokens]
    for git_index, token in enumerate(lowered):
        if token != "git":
            continue

        push_index = _find_git_push_index(lowered, git_index + 1)
        if push_index is None:
            continue

        push_args = lowered[push_index + 1 :]
        if any(arg in {"--force", "-f", "--force-with-lease"} for arg in push_args):
            return True

    return False


def _find_git_push_index(tokens: list[str], start: int) -> int | None:
    index = start
    while index < len(tokens):
        token = tokens[index]

        if token == "push":
            return index

        if token in {"-c", "-C", "--git-dir", "--work-tree", "--namespace"}:
            index += 2
            continue

        if token.startswith("-"):
            index += 1
            continue

        return None

    return None


def _has_delete_from_without_where(command: str) -> bool:
    for statement in _split_statements(command):
        if DELETE_FROM_PATTERN.search(statement) and not WHERE_PATTERN.search(statement):
            return True
    return False


def _split_statements(command: str) -> list[str]:
    return [
        statement.strip()
        for statement in re.split(r";|&&|\|\|", command)
        if statement.strip()
    ]


def _blocked_log_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }

    log_path = _blocked_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_deny_output(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command: {reason}. "
                "The attempted command was logged to ~/.claude/hooks/blocked.log."
            ),
        }
    }


def main() -> int:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return 0

    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or payload.get("project_path") or "")
    try:
        log_blocked_attempt(command, project_path, reason)
    except OSError:
        pass

    print(json.dumps(build_deny_output(reason), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
