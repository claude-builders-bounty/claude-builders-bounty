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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


SQL_KEYWORDS = re.compile(r"\b(DROP\s+TABLE|TRUNCATE)\b", re.IGNORECASE)
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_recursive_force_rm(command: str) -> bool:
    words = shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue
        for candidate in words[index + 1 :]:
            if not candidate.startswith("-") or candidate == "--":
                break
            compact = candidate.replace("-", "")
            if "r" in compact.lower() and "f" in compact.lower():
                return True
    return bool(re.search(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f|(^|[;&|]\s*)rm\s+-[A-Za-z]*f[A-Za-z]*r", command))


def has_force_push(command: str) -> bool:
    words = shell_words(command)
    for index, word in enumerate(words[:-2]):
        if word == "git" and words[index + 1] == "push":
            push_args = words[index + 2 :]
            return any(arg == "--force" or arg.startswith("--force=") for arg in push_args)
    return False


def delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if DELETE_FROM.search(statement) and not WHERE_CLAUSE.search(statement):
            return True
    return False


def block_reason(command: str) -> str | None:
    if has_recursive_force_rm(command):
        return "Blocked recursive forced deletion pattern: rm -rf"
    if has_force_push(command):
        return "Blocked forced git push: git push --force"
    if SQL_KEYWORDS.search(command):
        return "Blocked destructive SQL command: DROP TABLE or TRUNCATE"
    if delete_without_where(command):
        return "Blocked DELETE FROM without a WHERE clause"
    return None


def log_block(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": cwd,
        "attempted_command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str, command: str, cwd: str) -> None:
    log_block(command, cwd, reason)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{reason}. The command was not executed. "
                f"Review the command and use a safer, explicit alternative if intended."
            ),
        }
    }))


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
    command = str(tool_input.get("command") or "")
    cwd = str(payload.get("cwd") or os.getcwd())

    reason = block_reason(command)
    if reason:
        deny(reason, command, cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
