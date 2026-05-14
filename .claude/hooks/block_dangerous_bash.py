#!/usr/bin/env python3
"""PreToolUse hook that denies destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable


HOOK_NAME = "PreToolUse"


def _tokenize(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return shlex.split(command, posix=False)


def _short_option_has(option: str, flag: str) -> bool:
    return option.startswith("-") and not option.startswith("--") and flag in option[1:]


def _has_rm_force_recursive(tokens: Iterable[str]) -> bool:
    tokens = list(tokens)
    separators = {";", "&&", "||", "|", "(", ")"}

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        has_force = False
        has_recursive = False

        for next_token in tokens[index + 1 :]:
            if next_token in separators:
                break
            if not next_token.startswith("-"):
                break

            has_force = has_force or _short_option_has(next_token, "f") or next_token == "--force"
            has_recursive = (
                has_recursive
                or _short_option_has(next_token, "r")
                or _short_option_has(next_token, "R")
                or next_token in {"--recursive", "--dir"}
            )

            if has_force and has_recursive:
                return True

    return False


def _has_force_push(tokens: Iterable[str]) -> bool:
    tokens = list(tokens)
    separators = {";", "&&", "||", "|", "(", ")"}

    for index, token in enumerate(tokens):
        if token != "git":
            continue

        command_tokens: list[str] = []
        for next_token in tokens[index + 1 :]:
            if next_token in separators:
                break
            command_tokens.append(next_token)

        if not command_tokens or command_tokens[0] != "push":
            continue

        for option in command_tokens[1:]:
            if option in {"-f", "--force", "--force-with-lease"}:
                return True
            if option.startswith("--force=") or option.startswith("--force-with-lease="):
                return True

    return False


def _has_delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        delete_match = re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE)
        if delete_match and not re.search(r"\bwhere\b", statement[delete_match.end() :], re.IGNORECASE):
            return True
    return False


def _danger_reason(command: str) -> str | None:
    tokens = _tokenize(command)

    if _has_rm_force_recursive(tokens):
        return "rm with both recursive and force flags can delete entire directory trees"
    if re.search(r"\bdrop\s+table\b", command, re.IGNORECASE):
        return "DROP TABLE can destroy database schema and data"
    if re.search(r"\btruncate(?:\s+table)?\b", command, re.IGNORECASE):
        return "TRUNCATE can erase table contents without row-level review"
    if _has_delete_without_where(command):
        return "DELETE FROM without a WHERE clause can erase every row"
    if _has_force_push(tokens):
        return "git push with force can rewrite remote branch history"

    return None


def _project_path(payload: dict) -> str:
    return (
        payload.get("cwd")
        or payload.get("project_path")
        or payload.get("workspace")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def _log_block(command: str, reason: str, payload: dict) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_path": _project_path(payload),
        "attempted_command": command,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_NAME,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked dangerous Bash command: "
                        f"{reason}. Revise the command into a safer form or ask the user before proceeding."
                    ),
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = _danger_reason(command)
    if not reason:
        return 0

    _log_block(command, reason, payload)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
