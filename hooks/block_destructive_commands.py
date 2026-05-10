#!/usr/bin/env python3
"""Claude Code PreToolUse hook for blocking destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockReason:
    label: str
    detail: str


def _compact_command(command: str, limit: int = 500) -> str:
    command = re.sub(r"\s+", " ", command).strip()
    if len(command) <= limit:
        return command
    return f"{command[:limit - 3]}..."


def _contains_recursive_force_rm(command: str) -> bool:
    """Detect rm invocations where force and recursive flags are both present."""
    rm_pattern = re.compile(
        r"""
        (?:(?<=^)|(?<=[;&|({\n]))      # start of a shell command
        \s*(?:sudo\s+)?rm\s+
        (?P<args>(?:-[A-Za-z]*[rf][A-Za-z]*\s+|--[^\s]+\s+){1,})
        """,
        re.VERBOSE,
    )
    for match in rm_pattern.finditer(command):
        short_flags = "".join(re.findall(r"(?<!-)-([A-Za-z]+)", match.group("args")))
        if "r" in short_flags and "f" in short_flags:
            return True
    return False


def _contains_force_push(command: str) -> bool:
    push_pattern = re.compile(
        r"""
        (?:(?<=^)|(?<=[;&|({\n]))
        \s*git\s+push\b
        (?P<args>[^;&|\n]*)
        """,
        re.VERBOSE,
    )
    for match in push_pattern.finditer(command):
        args = match.group("args")
        if re.search(r"(^|\s)(?:-f|--force(?:-with-lease)?)(?:\s|=|$)", args):
            return True
    return False


def _delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement = command[match.end():]
        statement = re.split(r";|\n", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    """Return the first destructive command rule matched by a shell command."""
    if _contains_recursive_force_rm(command):
        return BlockReason("rm -rf", "recursive forced removal can delete large parts of the filesystem")

    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return BlockReason("DROP TABLE", "dropping a table destroys database structure and data")

    if _contains_force_push(command):
        return BlockReason("git push --force", "force-pushing can overwrite shared branch history")

    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return BlockReason("TRUNCATE", "truncate removes all rows from a table")

    if _delete_without_where(command):
        return BlockReason("DELETE FROM without WHERE", "unqualified deletes can remove every row in a table")

    return None


def _log_blocked_attempt(command: str, reason: BlockReason, cwd: str | None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cwd": cwd or os.getcwd(),
        "reason": reason.label,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny(reason: BlockReason, command: str, log_error: Exception | None = None) -> dict[str, Any]:
    message = (
        f"Blocked destructive command: {reason.label}. "
        f"{reason.detail}. Review and rewrite the command before proceeding. "
        f"Command: {_compact_command(command)}"
    )
    if log_error is not None:
        message += f" Log write failed: {log_error}."
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }


def handle_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Return a Claude Code hook response, or None when the command is allowed."""
    if event.get("hook_event_name") != "PreToolUse":
        return None
    if event.get("tool_name") != "Bash":
        return None

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return None

    reason = find_block_reason(command)
    if reason is None:
        return None

    log_error = None
    try:
        _log_blocked_attempt(command, reason, event.get("cwd"))
    except OSError as exc:
        log_error = exc
    return _deny(reason, command, log_error)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook input JSON: {exc}", file=sys.stderr)
        return 1

    response = handle_event(event)
    if response is not None:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
