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


BLOCKED_LOG_ENV = "CLAUDE_HOOKS_BLOCKED_LOG"


def read_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive-bash-guard: invalid hook JSON: {exc}", file=sys.stderr)
        sys.exit(0)


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    if isinstance(command, str):
        return command
    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    env_path = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_path:
        return env_path

    return os.getcwd()


def strip_sql_comments(command: str) -> str:
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    command = re.sub(r"--[^\n\r]*", " ", command)
    return command


def contains_rm_rf(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        flag_tokens: list[str] = []
        for next_token in tokens[index + 1 :]:
            if not next_token.startswith("-") or next_token == "--":
                break
            flag_tokens.append(next_token)

        combined_flags = "".join(flag.lstrip("-").lower() for flag in flag_tokens)
        if "r" in combined_flags and "f" in combined_flags:
            return True

    return False


def delete_from_without_where(sql: str) -> bool:
    for statement in sql.split(";"):
        normalized = " ".join(statement.split())
        if not re.search(r"\bdelete\s+from\b", normalized, flags=re.IGNORECASE):
            continue
        if not re.search(r"\bwhere\b", normalized, flags=re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    scrubbed = strip_sql_comments(command)

    if contains_rm_rf(command):
        return "rm with recursive and force flags can delete large parts of the filesystem"

    if re.search(r"\bdrop\s+table\b", scrubbed, flags=re.IGNORECASE):
        return "DROP TABLE can permanently remove database schema and data"

    if re.search(r"\btruncate\b", scrubbed, flags=re.IGNORECASE):
        return "TRUNCATE can permanently remove all rows from a table"

    if delete_from_without_where(scrubbed):
        return "DELETE FROM without a WHERE clause can remove every row in a table"

    if re.search(r"\bgit\s+push\b(?=[^\n\r;]*\s--force(?:-with-lease)?\b)", command, flags=re.IGNORECASE):
        return "force-pushing can overwrite shared Git history"

    return None


def log_path() -> Path:
    override = os.environ.get(BLOCKED_LOG_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command: str, cwd: str, reason: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = read_payload()
    command = extract_command(payload)

    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    cwd = project_path(payload)
    log_blocked(command, cwd, reason)
    print(
        "Blocked unsafe Bash command before execution.\n"
        f"Reason: {reason}.\n"
        "Use a narrower, reversible command or ask the user for explicit approval.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
