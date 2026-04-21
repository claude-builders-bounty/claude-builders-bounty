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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.getcwd()


def _has_rm_rf(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token not in {"rm", "/bin/rm", "sudo"}:
            continue

        rm_index = index
        if token == "sudo":
            if index + 1 >= len(tokens) or tokens[index + 1] not in {"rm", "/bin/rm"}:
                continue
            rm_index = index + 1

        flags = ""
        for arg in tokens[rm_index + 1 :]:
            if not arg.startswith("-"):
                continue
            flags += arg.lstrip("-")
        if "r" in flags and "f" in flags:
            return True
    return False


def _delete_from_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement = command[match.start() :].split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    if _has_rm_rf(command):
        return "Blocked destructive filesystem command: rm -rf."
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "Blocked destructive SQL command: DROP TABLE."
    if re.search(r"\bgit\s+push\b[^\n;]*--force(?:\s|$)", command, flags=re.IGNORECASE):
        return "Blocked destructive Git command: git push --force."
    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return "Blocked destructive SQL command: TRUNCATE."
    if _delete_from_without_where(command):
        return "Blocked unsafe SQL command: DELETE FROM without a WHERE clause."
    return None


def _log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "command": command,
            "project_path": project_path,
            "reason": reason,
        },
        ensure_ascii=False,
    )
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_blocked_attempt(command, project_path, reason)
    print(
        f"{reason}\n"
        f"Project: {project_path}\n"
        "Choose a safer command, add a narrow WHERE clause, or ask the user for an explicit manual override.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
