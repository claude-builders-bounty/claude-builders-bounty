#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def _extract_command(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    value = payload.get("cwd")
    if isinstance(value, str) and value:
        return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _split_shell(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _rm_recursive_force(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        options = []
        for next_token in tokens[index + 1 :]:
            if not next_token.startswith("-"):
                break
            options.append(next_token)

        short_flags = "".join(
            opt[1:] for opt in options if opt.startswith("-") and not opt.startswith("--")
        )
        has_recursive = "r" in short_flags or "R" in short_flags or "--recursive" in options
        has_force = "f" in short_flags or "--force" in options
        if has_recursive and has_force:
            return True
    return False


def _force_push(tokens: list[str]) -> bool:
    for index in range(len(tokens) - 2):
        if tokens[index] == "git" and tokens[index + 1] == "push":
            push_args = tokens[index + 2 :]
            return any(arg in {"--force", "-f", "--force-with-lease"} for arg in push_args)
    return False


def _delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement = command[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    tokens = _split_shell(command)
    if _rm_recursive_force(tokens):
        return "recursive force delete commands such as rm -rf are blocked"
    if _force_push(tokens):
        return "force-pushing with git push --force/-f is blocked"
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "DROP TABLE statements are blocked"
    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return "TRUNCATE statements are blocked"
    if _delete_without_where(command):
        return "DELETE FROM statements without a WHERE clause are blocked"
    return None


def _log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _utc_now(),
        "command": command,
        "project_path": _project_path(payload),
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict):
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    _log_block(payload, command, reason)
    print(
        "Blocked destructive Bash command: "
        f"{reason}. Command was not executed: {command}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
