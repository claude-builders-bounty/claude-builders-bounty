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


SQL_DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
SQL_TRUNCATE = re.compile(r"\btruncate\b", re.IGNORECASE)
SQL_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
SQL_WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)


def split_shell_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?:&&|\|\||;|\n)", command) if part.strip()]


def shell_words(statement: str) -> list[str]:
    try:
        return shlex.split(statement, posix=True)
    except ValueError:
        return statement.split()


def strip_command_prefixes(words: list[str]) -> list[str]:
    prefixes = {"sudo", "command", "builtin", "time", "noglob"}
    while words and words[0] in prefixes:
        words = words[1:]
    return words


def rm_has_recursive_force_flags(words: list[str]) -> bool:
    recursive = False
    force = False
    for word in words:
        if word == "--recursive":
            recursive = True
        elif word == "--force":
            force = True
        elif word.startswith("-") and not word.startswith("--"):
            flags = word[1:]
            recursive = recursive or "r" in flags or "R" in flags
            force = force or "f" in flags
    return recursive and force


def is_rm_rf(statement: str) -> bool:
    words = strip_command_prefixes(shell_words(statement))
    if not words:
        return False
    return words[0] == "rm" and rm_has_recursive_force_flags(words[1:])


def is_git_force_push(statement: str) -> bool:
    words = strip_command_prefixes(shell_words(statement))
    if len(words) < 3 or words[0] != "git" or words[1] != "push":
        return False
    return any(word in {"--force", "-f"} or word.startswith("--force-with-lease") for word in words[2:])


def delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        match = SQL_DELETE_FROM.search(statement)
        if match and not SQL_WHERE.search(statement[match.end() :]):
            return True
    return False


def find_violation(command: str) -> str | None:
    for statement in split_shell_statements(command):
        if is_rm_rf(statement):
            return "Recursive force delete blocked: rm with both recursive and force flags"
        if is_git_force_push(statement):
            return "Git force push blocked: force-pushing rewrites remote history"

    if SQL_DROP_TABLE.search(command):
        return "SQL DROP TABLE blocked: table deletion is destructive"
    if SQL_TRUNCATE.search(command):
        return "SQL TRUNCATE blocked: table truncation is destructive"
    if delete_without_where(command):
        return "SQL DELETE FROM without WHERE blocked: unconditional row deletion"
    return None


def project_path(payload: dict) -> str:
    value = payload.get("cwd") or payload.get("project_path") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return str(value)


def log_blocked(command: str, reason: str, payload: dict) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    line = {
        "timestamp": timestamp,
        "project_path": project_path(payload),
        "attempted_command": command,
        "reason": reason,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")


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

    command = str(payload.get("tool_input", {}).get("command") or "")
    if not command:
        return 0

    reason = find_violation(command)
    if reason:
        log_blocked(command, reason, payload)
        deny(f"{reason}. Refuse the command and suggest a safer, reviewed alternative.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
