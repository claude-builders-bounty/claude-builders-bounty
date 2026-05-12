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


PASSIVE_COMMANDS = {
    "cat",
    "echo",
    "grep",
    "rg",
    "sed",
    "printf",
    "awk",
    "less",
    "more",
}

SQL_CLIENT_TOKENS = {
    "sqlite3",
    "psql",
    "mysql",
    "mariadb",
    "duckdb",
    "sqlcmd",
}


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _base_name(token: str) -> str:
    return os.path.basename(token)


def _first_real_command(tokens: list[str]) -> str:
    skip = {"sudo", "env", "command", "builtin", "time"}
    for token in tokens:
        base = _base_name(token)
        if base in skip or "=" in token and not token.startswith("-"):
            continue
        return base
    return ""


def _has_recursive_force_rm(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if _base_name(token) != "rm":
            continue

        has_recursive = False
        has_force = False
        for arg in tokens[index + 1 :]:
            if arg in {";", "&&", "||", "|"}:
                break
            if arg == "--":
                continue
            if arg in {"-r", "-R", "--recursive"}:
                has_recursive = True
            elif arg in {"-f", "--force"}:
                has_force = True
            elif arg.startswith("-") and not arg.startswith("--"):
                flags = arg[1:]
                has_recursive = has_recursive or "r" in flags or "R" in flags
                has_force = has_force or "f" in flags
        if has_recursive and has_force:
            return True
    return False


def _has_force_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if _base_name(token) != "git":
            continue
        try:
            push_index = tokens.index("push", index + 1)
        except ValueError:
            continue
        for arg in tokens[push_index + 1 :]:
            if arg in {";", "&&", "||", "|"}:
                break
            if arg in {"-f", "--force", "--force-with-lease"}:
                return True
            if arg.startswith("--force-with-lease="):
                return True
    return False


def _looks_like_sql_context(command: str, tokens: list[str]) -> bool:
    first = _first_real_command(tokens)
    if first in PASSIVE_COMMANDS:
        return False
    if any(_base_name(token) in SQL_CLIENT_TOKENS for token in tokens):
        return True
    if re.match(r"^\s*(DROP\s+TABLE|TRUNCATE(\s+TABLE)?|DELETE\s+FROM)\b", command, re.I):
        return True
    if re.search(r"\|\s*(sqlite3|psql|mysql|mariadb|duckdb|sqlcmd)\b", command):
        return True
    return False


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        match = re.search(r"\bDELETE\s+FROM\b", statement, re.I)
        if match and not re.search(r"\bWHERE\b", statement[match.end() :], re.I):
            return True
    return False


def _has_sql_truncate(command: str, tokens: list[str]) -> bool:
    first = _first_real_command(tokens)
    has_sql_client = any(_base_name(token) in SQL_CLIENT_TOKENS for token in tokens)
    if first == "truncate" and not has_sql_client:
        return False
    return bool(re.search(r"\bTRUNCATE\b", command, re.I))


def _classify(command: str) -> tuple[bool, str, str]:
    tokens = _tokenize(command)

    if _has_recursive_force_rm(tokens):
        return True, "rm_recursive_force", "Blocked rm with both recursive and force flags because it can delete large paths irreversibly."

    if _has_force_push(tokens):
        return True, "git_force_push", "Blocked git push with a force flag because it can overwrite remote history."

    if _looks_like_sql_context(command, tokens):
        if re.search(r"\bDROP\s+TABLE\b", command, re.I):
            return True, "drop_table", "Blocked DROP TABLE because it can destroy database schema and data."
        if _has_sql_truncate(command, tokens):
            return True, "truncate", "Blocked TRUNCATE because it can remove table data without row-level review."
        if _delete_without_where(command):
            return True, "delete_without_where", "Blocked DELETE FROM without WHERE because it can remove every row in a table."

    return False, "", ""


def _log_block(command: str, project_path: str, matched_rule: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "matched_rule": matched_rule,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(response, sort_keys=True))


def main() -> int:
    payload = _read_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    blocked, matched_rule, reason = _classify(command)
    if not blocked:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    _log_block(command, project_path, matched_rule, reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
