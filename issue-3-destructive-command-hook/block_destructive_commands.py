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
from typing import Any, TextIO


LOG_PATH_ENV = "BLOCK_DESTRUCTIVE_COMMANDS_LOG_PATH"


def command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_recursive_force(command: str) -> bool:
    tokens = command_tokens(command)
    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        flags: list[str] = []
        for next_token in tokens[index + 1 :]:
            if next_token in {";", "&&", "||", "|"}:
                break
            if next_token.startswith("-"):
                flags.append(next_token)
        has_recursive = any(
            flag in {"-r", "-R", "--recursive"}
            or (flag.startswith("-") and not flag.startswith("--") and "r" in flag.lower())
            for flag in flags
        )
        has_force = any(
            flag == "--force"
            or (flag.startswith("-") and not flag.startswith("--") and "f" in flag.lower())
            for flag in flags
        )
        if has_recursive and has_force:
            return True
    return False


def delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = re.split(r";|\n|\r|&&|\|\|", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    checks = [
        (has_rm_recursive_force(command), "rm recursive force command"),
        (
            re.search(r"\bdrop\s+table\b", command, re.IGNORECASE) is not None,
            "DROP TABLE statement",
        ),
        (
            re.search(r"\bgit\s+push\b[^\n\r;|&]*--force(?:\b|=)", command, re.IGNORECASE)
            is not None,
            "git push --force",
        ),
        (re.search(r"\btruncate\b", command, re.IGNORECASE) is not None, "TRUNCATE statement"),
        (delete_without_where(command), "DELETE FROM without WHERE"),
    ]
    for matched, reason in checks:
        if matched:
            return reason
    return None


def blocked_log_path() -> Path:
    override = os.environ.get(LOG_PATH_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def write_block_log(command: str, project_path: str, reason: str) -> None:
    path = blocked_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "attempted_command": command,
    }
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny_output(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command: {reason}. "
                "The command was not executed."
            ),
        }
    }


def load_event(stdin: TextIO) -> dict[str, Any] | None:
    raw_input = stdin.read()
    if not raw_input.strip():
        return None
    try:
        event = json.loads(raw_input)
    except json.JSONDecodeError:
        return None
    return event if isinstance(event, dict) else None


def main(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    event = load_event(stdin)
    if not event:
        return 0

    if event.get("hook_event_name") not in {None, "PreToolUse"}:
        return 0
    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = str(event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or "")
    try:
        write_block_log(command, project_path, reason)
    except OSError:
        pass

    stdout.write(json.dumps(deny_output(reason), separators=(",", ":")))
    stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
