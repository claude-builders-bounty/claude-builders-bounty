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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def normalize_sql(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip()).lower()


def split_shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(command: str) -> bool:
    words = split_shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue

        for option in words[index + 1 :]:
            if option == "--":
                break
            if not option.startswith("-"):
                continue
            short_options = option.lstrip("-")
            if "r" in short_options and "f" in short_options:
                return True
    return False


def has_drop_table(command: str) -> bool:
    if is_text_search_command(command):
        return False
    return re.search(r"\bdrop\s+table\b", normalize_sql(command)) is not None


def has_truncate(command: str) -> bool:
    if is_text_search_command(command):
        return False
    return re.search(r"\btruncate(?:\s+table)?\b", normalize_sql(command)) is not None


def has_delete_without_where(command: str) -> bool:
    if is_text_search_command(command):
        return False
    sql = normalize_sql(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql):
        statement = sql[match.start() :]
        statement = re.split(r";|&&|\|\||\n", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement):
            return True
    return False


def is_text_search_command(command: str) -> bool:
    words = split_shell_words(command)
    return bool(words) and words[0] in {"grep", "egrep", "fgrep", "rg", "ag"}


def has_force_push(command: str) -> bool:
    words = split_shell_words(command)
    if len(words) < 3:
        return False

    for index in range(len(words) - 2):
        if words[index] != "git" or words[index + 1] != "push":
            continue
        push_args = words[index + 2 :]
        if "--force" in push_args or "--force-with-lease" in push_args:
            return True
        if any(arg.startswith("-") and "f" in arg.lstrip("-") for arg in push_args):
            return True
    return False


def block_reason(command: str) -> str | None:
    checks = [
        (has_rm_rf, "rm -rf style recursive forced deletion"),
        (has_force_push, "forced git push"),
        (has_drop_table, "DROP TABLE statement"),
        (has_truncate, "TRUNCATE statement"),
        (has_delete_without_where, "DELETE FROM statement without a WHERE clause"),
    ]

    for check, reason in checks:
        if check(command):
            return reason
    return None


def read_hook_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Could not parse Claude Code hook JSON input: {exc}", file=sys.stderr)
        sys.exit(1)


def append_block_log(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project_path = project_path.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp}\t{safe_project_path}\t{reason}\t{safe_command}\n",
        )


def main() -> int:
    payload = read_hook_input()

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or command.strip() == "":
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or ""
    append_block_log(command, project_path, reason)

    print(
        "Blocked destructive Bash command before execution. "
        f"Reason: {reason}. "
        "Use a safer command, add a restrictive WHERE clause, or ask the user "
        "for an explicit manual action if this destructive operation is truly intended.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
