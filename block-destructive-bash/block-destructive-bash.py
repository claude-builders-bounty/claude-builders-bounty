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


BLOCK_RESPONSE = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "",
    }
}


def _shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _has_recursive_force_rm(command: str) -> bool:
    words = _shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue

        has_recursive = False
        has_force = False
        for option in words[index + 1 :]:
            if not option.startswith("-") or option == "--":
                break
            compact = option.lstrip("-")
            has_recursive = has_recursive or "r" in compact or "R" in compact or compact == "recursive"
            has_force = has_force or "f" in compact or compact == "force"
            if has_recursive and has_force:
                return True

    return False


def _has_force_push(command: str) -> bool:
    words = _shell_words(command)
    for index, word in enumerate(words[:-2]):
        if word != "git":
            continue
        if words[index + 1] != "push":
            continue
        if any(arg == "--force" or arg == "-f" or arg.startswith("--force-with-lease") for arg in words[index + 2 :]):
            return True
    return False


def _sql_statement_segments(command: str) -> list[str]:
    return [segment.strip() for segment in re.split(r";|\n", command) if segment.strip()]


def _has_delete_without_where(command: str) -> bool:
    for statement in _sql_statement_segments(command):
        normalized = re.sub(r"\s+", " ", statement, flags=re.IGNORECASE).strip()
        if re.search(r"\bDELETE\s+FROM\b", normalized, flags=re.IGNORECASE) and not re.search(
            r"\bWHERE\b", normalized, flags=re.IGNORECASE
        ):
            return True
    return False


def _is_plain_text_command(command: str) -> bool:
    words = _shell_words(command)
    if not words:
        return False

    text_commands = {
        "ack",
        "ag",
        "cat",
        "echo",
        "grep",
        "head",
        "less",
        "more",
        "printf",
        "rg",
        "sed",
        "tail",
    }
    return Path(words[0]).name in text_commands


def _has_destructive_sql(command: str) -> str | None:
    if _is_plain_text_command(command):
        return None

    if re.search(r"\bDROP\s+TABLE\b", command, flags=re.IGNORECASE):
        return "Blocked DROP TABLE statement"

    if re.search(r"\bTRUNCATE\b", command, flags=re.IGNORECASE):
        return "Blocked TRUNCATE statement"

    if _has_delete_without_where(command):
        return "Blocked DELETE FROM statement without WHERE clause"

    return None


def block_reason(command: str) -> str | None:
    if _has_recursive_force_rm(command):
        return "Blocked destructive rm command with recursive and force flags"

    if _has_force_push(command):
        return "Blocked force push command"

    return _has_destructive_sql(command)


def _log_path() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


def _deny(reason: str) -> None:
    response = json.loads(json.dumps(BLOCK_RESPONSE))
    response["hookSpecificOutput"]["permissionDecisionReason"] = reason
    print(json.dumps(response, separators=(",", ":")))


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = block_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    log_blocked_attempt(command, project_path, reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
