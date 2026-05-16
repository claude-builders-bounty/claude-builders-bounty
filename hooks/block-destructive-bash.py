#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the PreToolUse JSON payload from stdin. If the tool call is a Bash
command matching a destructive pattern, writes a denial decision to stdout and
logs the blocked attempt to ~/.claude/hooks/blocked.log.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any

SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd"}
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_TABLE_RE = re.compile(r"\btruncate\s+(?:table\s+)?[\w.\"`]+", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def project_path(payload: dict[str, Any]) -> str:
    return str(
        payload.get("cwd")
        or payload.get("project_dir")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return command.split()


def is_sql_command(command: str, words: list[str]) -> bool:
    return any(Path(word).name.lower() in SQL_CLIENTS for word in words) or command.lstrip().lower().startswith(
        ("drop table", "truncate", "delete from")
    )


def has_forced_recursive_rm(words: list[str]) -> bool:
    for index, word in enumerate(words):
        if Path(word).name != "rm":
            continue

        flags = words[index + 1 :]
        has_recursive = False
        has_force = False
        for flag in flags:
            if flag == "--":
                break
            if not flag.startswith("-"):
                break
            if flag in {"--recursive", "--dir"}:
                has_recursive = True
            elif flag == "--force":
                has_force = True
            elif flag.startswith("--"):
                continue
            else:
                has_recursive = has_recursive or "r" in flag or "R" in flag
                has_force = has_force or "f" in flag
        if has_recursive and has_force:
            return True
    return False


def has_forced_git_push(words: list[str]) -> bool:
    for index in range(len(words) - 1):
        if Path(words[index]).name != "git" or words[index + 1] != "push":
            continue
        args = words[index + 2 :]
        return any(
            arg in {"-f", "--force", "--force-with-lease"}
            or arg.startswith("--force=")
            or arg.startswith("--force-with-lease=")
            for arg in args
        )
    return False


def sql_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n", command) if part.strip()]


def delete_without_where(command: str) -> bool:
    """Return True for DELETE FROM statements with no WHERE before statement end."""
    return any(DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement) for statement in sql_statements(command))


def blocked_reason(command: str) -> str | None:
    words = shell_words(command)

    if has_forced_recursive_rm(words):
        return "Recursive forced deletion is blocked. Matched pattern: rm with recursive and force flags."

    if has_forced_git_push(words):
        return "Forced git push is blocked. Matched pattern: git push with force flag."

    if is_sql_command(command, words):
        if DROP_TABLE_RE.search(command):
            return "DROP TABLE is blocked. Matched SQL pattern: DROP TABLE."
        if TRUNCATE_TABLE_RE.search(command):
            return "TRUNCATE is blocked. Matched SQL pattern: TRUNCATE TABLE."
        if delete_without_where(command):
            return "DELETE FROM without a WHERE clause is blocked. Matched SQL pattern: DELETE FROM without WHERE."

    return None


def log_block(command: str, path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\tproject={path}\treason={reason}\tcommand={safe_command}\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            separators=(",", ":"),
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
    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    path = project_path(payload)
    log_block(command, path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
