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


HOOK_EVENT_NAME = "PreToolUse"
BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if Path(token).name != "rm":
            continue

        recursive = False
        forced = False
        for option in tokens[index + 1 :]:
            if not option.startswith("-"):
                break
            if option in {"--recursive", "--dir"}:
                recursive = True
            if option in {"--force"}:
                forced = True
            if option.startswith("-") and not option.startswith("--"):
                flags = option.lstrip("-").lower()
                recursive = recursive or "r" in flags
                forced = forced or "f" in flags
            if recursive and forced:
                return True
    return False


def has_git_force_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if Path(token).name != "git":
            continue

        after_git = tokens[index + 1 :]
        try:
            push_index = after_git.index("push")
        except ValueError:
            continue

        for option in after_git[push_index + 1 :]:
            if option in {"--force", "-f"} or option.startswith("--force-with-lease"):
                return True
            if option.startswith("-") and "f" in option.lstrip("-"):
                return True
    return False


def delete_from_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        statement = command[match.start() :].split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def find_violation(command: str) -> str | None:
    tokens = shell_tokens(command)

    if has_rm_rf(tokens):
        return "rm -rf"
    if has_git_force_push(tokens):
        return "git push --force"
    if DROP_TABLE_RE.search(command):
        return "DROP TABLE"
    if TRUNCATE_RE.search(command):
        return "TRUNCATE"
    if delete_from_without_where(command):
        return "DELETE FROM without WHERE"
    return None


def log_blocked_attempt(command: str, project_path: str, rule: str, log_path: Path = BLOCKED_LOG) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "attempted_command": command,
        "project_path": project_path,
        "matched_rule": rule,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(rule: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command matching '{rule}'. "
                "Revise the command or ask the user to run it manually."
            ),
        }
    }


def command_from_payload(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def handle_payload(payload: dict[str, Any], log_path: Path = BLOCKED_LOG) -> dict[str, Any] | None:
    command = command_from_payload(payload)
    if not command:
        return None

    rule = find_violation(command)
    if rule is None:
        return None

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked_attempt(command, project_path, rule, log_path)
    return deny(rule)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Invalid Claude Code hook payload: {error}", file=sys.stderr)
        return 1

    response = handle_payload(payload)
    if response is not None:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
