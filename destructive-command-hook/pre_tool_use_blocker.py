#!/usr/bin/env python3
"""Block destructive Bash commands from Claude Code PreToolUse hooks."""

from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import sys
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def find_block_reason(command: str) -> str | None:
    stripped = command.strip()
    lower = stripped.lower()

    if is_rm_rf(stripped):
        return "`rm -rf` style recursive force deletion is blocked."
    if is_forced_git_push(stripped):
        return "Forced git pushes are blocked to avoid rewriting shared history."
    if re.search(r"\bdrop\s+table\b", lower):
        return "`DROP TABLE` is blocked because it can destroy schema and data."
    if re.search(r"\btruncate\b", lower):
        return "`TRUNCATE` is blocked because it can erase table contents."
    if has_delete_without_where(lower):
        return "`DELETE FROM` without a `WHERE` clause is blocked."
    return None


def is_rm_rf(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        flags = ""
        for following in tokens[index + 1 :]:
            if not following.startswith("-") or following == "--":
                break
            flags += following.lstrip("-")
        if "r" in flags and "f" in flags:
            return True

    return bool(re.search(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b|\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b", command))


def is_forced_git_push(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] == ["git", "push"]:
            push_args = tokens[index + 2 :]
            return any(
                arg == "-f"
                or arg == "--force"
                or arg == "--force-with-lease"
                or arg.startswith("--force=")
                or arg.startswith("--force-with-lease=")
                for arg in push_args
            )
    return False


def has_delete_without_where(command_lower: str) -> bool:
    statements = re.split(r";|\n", command_lower)
    for statement in statements:
        match = re.search(r"\bdelete\s+from\b", statement)
        if match and not re.search(r"\bwhere\b", statement[match.end() :]):
            return True
    return False


def log_blocked(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_cwd = cwd.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\t{safe_cwd}\t{safe_command}\t{reason}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    cwd = payload.get("cwd") or ""
    log_blocked(command, str(cwd), reason)
    print(f"Blocked Bash command: {reason}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

