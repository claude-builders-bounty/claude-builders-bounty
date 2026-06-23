#!/usr/bin/env python3
"""PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def has_rm_rf(tokens: Iterable[str]) -> bool:
    token_list = list(tokens)
    for index, token in enumerate(token_list):
        if token != "rm":
            continue

        has_recursive = False
        has_force = False

        for arg in token_list[index + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue
            if arg in {"--recursive", "--dir"}:
                has_recursive = True
            if arg == "--force":
                has_force = True
            if arg.startswith("-") and not arg.startswith("--"):
                flags = arg.lstrip("-")
                has_recursive = has_recursive or "r" in flags or "R" in flags
                has_force = has_force or "f" in flags

        if has_recursive and has_force:
            return True

    return False


def has_force_push(tokens: Iterable[str]) -> bool:
    token_list = list(tokens)
    for index, token in enumerate(token_list):
        if token != "git":
            continue
        if index + 1 >= len(token_list) or token_list[index + 1] != "push":
            continue
        push_args = token_list[index + 2 :]
        if any(arg in {"--force", "--force-with-lease", "-f"} for arg in push_args):
            return True
    return False


def has_delete_without_where(command: str) -> bool:
    for statement in re.split(r";|&&|\|\|", command):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    tokens = shell_tokens(command)

    if has_rm_rf(tokens):
        return "blocked recursive forced removal: rm -rf"
    if DROP_TABLE_RE.search(command):
        return "blocked destructive SQL: DROP TABLE"
    if has_force_push(tokens):
        return "blocked force push: git push --force"
    if TRUNCATE_RE.search(command):
        return "blocked destructive SQL/filesystem truncate command"
    if has_delete_without_where(command):
        return "blocked DELETE FROM statement without a WHERE clause"

    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    hook_dir = Path.home() / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    log_path = hook_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    log_line = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "attempted_command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(log_line, ensure_ascii=True) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Destructive command guard could not parse hook input: {exc}", file=sys.stderr)
        return 1

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    project_path = payload.get("cwd") or os.getcwd()

    if tool_name != "Bash" or not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    log_block(command, project_path, reason)
    print(
        "Claude Code blocked this Bash command before execution: "
        f"{reason}. Review the command and choose a safer alternative.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
