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


BLOCK_EXIT_CODE = 2


def default_log_path() -> Path:
    configured = os.environ.get("CLAUDE_BLOCK_HOOK_LOG")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def normalize_command(command: str) -> str:
    return " ".join(command.replace("\\\n", " ").split())


def split_sql_statements(command: str) -> list[str]:
    return [part.strip() for part in command.split(";") if part.strip()]


def has_rm_rf(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        for next_token in tokens[index + 1 :]:
            if next_token == "--":
                break
            if not next_token.startswith("-"):
                continue
            flags = next_token.lstrip("-")
            if "r" in flags and "f" in flags:
                return True
    return False


def has_git_force_push(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        tokens = command.split()

    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        if "--force" in push_args or "-f" in push_args:
            return True
        if any(arg.startswith("--force=") for arg in push_args):
            return True
    return False


def has_delete_without_where(command: str) -> bool:
    for statement in split_sql_statements(command):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b",
            statement,
            flags=re.IGNORECASE,
        ):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    normalized = normalize_command(command)
    if has_rm_rf(command):
        return "`rm -rf` style recursive forced deletion is blocked"
    if has_git_force_push(command):
        return "`git push --force` is blocked because it can rewrite shared history"
    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "`DROP TABLE` is blocked because it can destroy schema and data"
    if re.search(r"\btruncate\b", normalized, flags=re.IGNORECASE):
        return "`TRUNCATE` is blocked because it can erase table data"
    if has_delete_without_where(normalized):
        return "`DELETE FROM` without a `WHERE` clause is blocked"
    return None


def command_from_payload(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def log_blocked(command: str, project_path: str, reason: str, log_path: Path | None = None) -> None:
    log_path = log_path or default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    safe_project_path = project_path.replace("\r", "\\r").replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{safe_project_path}\t{reason}\t{safe_command}\n")


def handle(payload: dict[str, Any], log_path: Path | None = None) -> tuple[int, str]:
    if payload.get("hook_event_name") != "PreToolUse":
        return 0, ""
    if payload.get("tool_name") != "Bash":
        return 0, ""

    command = command_from_payload(payload)
    reason = blocked_reason(command)
    if not reason:
        return 0, ""

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked(command, project_path, reason, log_path=log_path)
    message = (
        f"Blocked destructive Bash command: {reason}.\n"
        "Choose a safer command, add a restrictive WHERE clause, or ask the user for explicit direction."
    )
    return BLOCK_EXIT_CODE, message


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block-destructive hook could not parse JSON input: {exc}", file=sys.stderr)
        return 1

    exit_code, message = handle(payload)
    if message:
        print(message, file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
