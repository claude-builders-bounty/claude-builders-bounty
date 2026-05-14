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


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_TABLE_RE = re.compile(r"\btruncate(?:\s+table)?\s+[a-zA-Z_][\w.]*", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)

COMMAND_SEPARATORS_RE = re.compile(r"(?:&&|\|\||;|\n|\|)")
DB_CLIENTS = {"duckdb", "mariadb", "mysql", "psql", "sqlite3", "sqlcmd"}
SHELL_WRAPPERS = {"bash", "dash", "fish", "sh", "zsh"}
PREFIX_COMMANDS = {"command", "doas", "nohup", "sudo", "time"}


def main() -> int:
    payload = _read_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    if not command.strip():
        return 0

    reason = analyze_command(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_blocked_attempt(command, project_path, reason)
    _deny(reason)
    return 0


def analyze_command(command: str) -> str | None:
    """Return a block reason when a Bash command is unsafe."""
    for segment in _command_segments(command):
        reason = _analyze_segment(segment)
        if reason is not None:
            return reason
    return None


def _read_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _command_segments(command: str) -> list[str]:
    return [segment.strip() for segment in COMMAND_SEPARATORS_RE.split(command) if segment.strip()]


def _analyze_segment(segment: str) -> str | None:
    tokens = _split_shell(segment)
    if not tokens:
        return None

    command_index = _command_index(tokens)
    if command_index >= len(tokens):
        return None

    executable = _basename(tokens[command_index])

    if executable in SHELL_WRAPPERS:
        nested = _shell_command_argument(tokens[command_index + 1 :])
        if nested:
            return analyze_command(nested)

    if executable == "rm" and _has_recursive_force_flags(tokens[command_index + 1 :]):
        return "rm with both recursive and force flags can delete large directory trees without confirmation"

    if executable == "git" and _is_force_push(tokens[command_index + 1 :]):
        return "git push with force options can overwrite remote history"

    if executable in DB_CLIENTS or _is_direct_sql_statement(tokens, command_index):
        return _analyze_sql(segment)

    return None


def _split_shell(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def _command_index(tokens: list[str]) -> int:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        executable = _basename(token)

        if _looks_like_assignment(token):
            index += 1
            continue

        if executable == "env":
            index += 1
            while index < len(tokens) and (_looks_like_assignment(tokens[index]) or tokens[index].startswith("-")):
                index += 1
            continue

        if executable in PREFIX_COMMANDS:
            index += 1
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 1
            continue

        return index

    return index


def _looks_like_assignment(token: str) -> bool:
    if token.startswith("-") or "=" not in token:
        return False
    name, _value = token.split("=", 1)
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))


def _basename(token: str) -> str:
    return os.path.basename(token).lower()


def _shell_command_argument(tokens: list[str]) -> str | None:
    for index, token in enumerate(tokens):
        if token == "-c" and index + 1 < len(tokens):
            return tokens[index + 1]
    return None


def _has_recursive_force_flags(tokens: list[str]) -> bool:
    flags: set[str] = set()
    for token in tokens:
        if token == "--":
            break
        if not token.startswith("-") or token == "-":
            continue
        if token in {"--force", "--recursive"}:
            flags.add("f" if token == "--force" else "r")
            continue
        if token.startswith("--"):
            continue
        flags.update(character.lower() for character in token[1:])
    return "r" in flags and "f" in flags


def _is_force_push(tokens: list[str]) -> bool:
    index = _skip_git_global_options(tokens)
    if index >= len(tokens) or tokens[index] != "push":
        return False

    push_args = tokens[index + 1 :]
    return any(
        argument in {"-f", "--force", "--force-with-lease"}
        or argument.startswith("--force=")
        or argument.startswith("--force-with-lease=")
        for argument in push_args
    )


def _skip_git_global_options(tokens: list[str]) -> int:
    index = 0
    options_with_values = {"-C", "-c", "--git-dir", "--namespace", "--work-tree"}
    while index < len(tokens):
        token = tokens[index]
        if token in options_with_values:
            index += 2
        elif token.startswith("--git-dir=") or token.startswith("--namespace=") or token.startswith("--work-tree="):
            index += 1
        elif token.startswith("-"):
            index += 1
        else:
            break
    return index


def _is_direct_sql_statement(tokens: list[str], command_index: int) -> bool:
    first = tokens[command_index].lower()
    second = tokens[command_index + 1].lower() if command_index + 1 < len(tokens) else ""
    return (first == "drop" and second == "table") or first in {"delete", "truncate"}


def _analyze_sql(text: str) -> str | None:
    if DROP_TABLE_RE.search(text):
        return "DROP TABLE can destroy schema and data"

    if TRUNCATE_TABLE_RE.search(text):
        return "TRUNCATE can remove all rows from a table"

    if _has_delete_without_where(text):
        return "DELETE FROM without a WHERE clause can remove all rows from a table"

    return None


def _has_delete_without_where(text: str) -> bool:
    for match in DELETE_FROM_RE.finditer(text):
        statement = text[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def _project_path(payload: dict[str, Any]) -> str:
    return (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.getcwd()
    )


def _log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason}. Use a safer command or ask for explicit human approval."
            ),
        }
    }
    print(json.dumps(response))


if __name__ == "__main__":
    raise SystemExit(main())
