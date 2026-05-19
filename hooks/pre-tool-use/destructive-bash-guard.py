#!/usr/bin/env python3
"""Block destructive Bash commands from Claude Code PreToolUse hooks."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _has_destructive_rm(command: str) -> bool:
    tokens = _shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        options = tokens[index + 1 :]
        compact_flags = "".join(
            option[1:]
            for option in options
            if option.startswith("-") and not option.startswith("--")
        )
        has_force = "f" in compact_flags or "--force" in options
        has_recursive = (
            "r" in compact_flags
            or "R" in compact_flags
            or "--recursive" in options
            or "--dir" in options
        )
        if has_force and has_recursive:
            return True

    return bool(re.search(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f", command))


def _has_forced_git_push(command: str) -> bool:
    tokens = _shell_tokens(command)
    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        return any(
            arg in {"-f", "--force"} or arg.startswith("--force=") or arg == "--force-with-lease"
            for arg in push_args
        )
    return False


def _has_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bDELETE\s+FROM\b(?P<body>.*?)(?:;|$)", command, re.IGNORECASE | re.DOTALL):
        if not re.search(r"\bWHERE\b", match.group("body"), re.IGNORECASE):
            return True
    return False


CHECKS: list[tuple[str, Callable[[str], bool], str]] = [
    (
        "rm -rf",
        _has_destructive_rm,
        "Recursive forced deletion is blocked. Use a narrower remove command or ask the user explicitly.",
    ),
    (
        "DROP TABLE",
        lambda command: bool(re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE)),
        "DROP TABLE is blocked because it can destroy database schema and data.",
    ),
    (
        "git push --force",
        _has_forced_git_push,
        "Forced git pushes are blocked. Use a normal push or ask the user for an explicit override path.",
    ),
    (
        "TRUNCATE",
        lambda command: bool(re.search(r"\bTRUNCATE\b", command, re.IGNORECASE)),
        "TRUNCATE is blocked because it can erase table contents.",
    ),
    (
        "DELETE FROM without WHERE",
        _has_delete_without_where,
        "DELETE FROM without a WHERE clause is blocked because it can delete every row.",
    ),
]


def _blocked_reason(command: str) -> str | None:
    normalized = _collapse_whitespace(command)
    for label, predicate, reason in CHECKS:
        if predicate(normalized):
            return f"Blocked destructive Bash command ({label}): {reason}"
    return None


def _project_path(payload: dict[str, object]) -> str:
    return (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or str(payload.get("cwd") or "")
        or os.getcwd()
    )


def _log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "attempted_command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
                "suppressOutput": True,
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Invalid Claude Code hook payload: {error}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = _blocked_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_blocked_attempt(command, project_path, reason)
    _deny(f"{reason}\nProject path: {project_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
