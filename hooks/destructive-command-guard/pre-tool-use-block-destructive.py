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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def read_event() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def split_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;\n]", command) if part.strip()]


def has_rm_rf(command: str) -> bool:
    for statement in split_statements(command):
        words = shell_words(statement)
        if not words or words[0] != "rm":
            continue

        short_flags = "".join(word[1:] for word in words[1:] if re.fullmatch(r"-[A-Za-z]+", word))
        long_flags = {word for word in words[1:] if word.startswith("--")}
        has_recursive = "r" in short_flags or "R" in short_flags or "--recursive" in long_flags
        has_force = "f" in short_flags or "--force" in long_flags
        if has_recursive and has_force:
            return True

    return re.search(r"(?i)(?:^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b", command) is not None


def has_force_push(command: str) -> bool:
    return (
        re.search(r"(?i)(?:^|[;&|]\s*)git\s+push\b[^\n;&|]*\s(?:--force(?:-with-lease)?|-f)\b", command)
        is not None
    )


def has_drop_table(command: str) -> bool:
    return re.search(r"(?is)\bdrop\s+table\b", command) is not None


def has_truncate(command: str) -> bool:
    return re.search(r"(?is)(?:^|[;&|]\s*)truncate\b|\btruncate\s+(?:table\s+)?[A-Za-z_]", command) is not None


def has_delete_without_where(command: str) -> bool:
    for statement in split_statements(command):
        if re.search(r"(?is)\bdelete\s+from\b", statement) and not re.search(r"(?is)\bwhere\b", statement):
            return True
    return False


CHECKS = (
    ("rm -rf", has_rm_rf, "recursive forced deletion can irreversibly remove project or system files"),
    ("DROP TABLE", has_drop_table, "DROP TABLE can destroy database schema and data"),
    ("git push --force", has_force_push, "force-pushing can overwrite shared Git history"),
    ("TRUNCATE", has_truncate, "TRUNCATE can erase table or file contents without row-level review"),
    ("DELETE FROM without WHERE", has_delete_without_where, "DELETE FROM without WHERE can remove every row"),
)


def blocked_reason(command: str) -> tuple[str, str] | None:
    for pattern, check, reason in CHECKS:
        if check(command):
            return pattern, reason
    return None


def project_path(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_path"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def log_block(event: dict[str, Any], command: str, pattern: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "attempted_command": command,
        "blocked_pattern": pattern,
        "reason": reason,
        "project_path": project_path(event),
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def deny(pattern: str, reason: str, command: str) -> None:
    message = (
        f"Blocked destructive Bash command: matched {pattern}. {reason}. "
        "Choose a safer command or ask the user for explicit recovery steps."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def main() -> int:
    event = read_event()
    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    match = blocked_reason(command)
    if match is None:
        return 0

    pattern, reason = match
    log_block(event, command, pattern, reason)
    deny(pattern, reason, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
