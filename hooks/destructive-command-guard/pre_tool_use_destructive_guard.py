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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

SAFE_TEXT_COMMANDS = {
    "cat",
    "echo",
    "egrep",
    "fgrep",
    "grep",
    "less",
    "more",
    "printf",
    "rg",
    "sed",
    "tail",
}

DATABASE_CLIENTS = {
    "mariadb",
    "mysql",
    "psql",
    "sqlite3",
}

SHELL_WORDS = {"bash", "sh", "zsh", "fish"}
COMMAND_SEPARATORS = {";", "&&", "||", "|", "&"}
SHELL_OPERATORS = COMMAND_SEPARATORS | {"(", ")", "{", "}"}


def split_command(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|(){}")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def normalize_sql(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def command_starts_with_safe_text_tool(tokens: list[str]) -> bool:
    for token in tokens:
        if token in SHELL_OPERATORS or (not token.startswith("-") and "=" in token):
            continue
        return Path(token).name in SAFE_TEXT_COMMANDS
    return False


def command_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []

    for token in tokens:
        if token in COMMAND_SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        if token not in {"(", ")", "{", "}"}:
            current.append(token)

    if current:
        segments.append(current)

    return segments


def command_name(tokens: list[str]) -> str | None:
    for token in tokens:
        if token in SHELL_OPERATORS or (not token.startswith("-") and "=" in token):
            continue
        return Path(token).name
    return None


def has_recursive_force_rm(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if Path(token).name != "rm":
            continue

        flags_after_rm = tokens[index + 1 :]
        has_recursive = False
        has_force = False

        for flag in flags_after_rm:
            if flag in SHELL_OPERATORS:
                break
            if flag == "--":
                continue
            if flag in {"--recursive", "--dir"}:
                has_recursive = True
            elif flag == "--force":
                has_force = True
            elif flag.startswith("-") and not flag.startswith("--"):
                has_recursive = has_recursive or "r" in flag.lower() or "R" in flag
                has_force = has_force or "f" in flag.lower()

        if has_recursive and has_force:
            return True

    return False


def has_forced_git_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if Path(token).name != "git":
            continue

        cursor = index + 1
        while cursor < len(tokens) and tokens[cursor] in {"-C", "-c"}:
            cursor += 2
        while cursor < len(tokens) and tokens[cursor].startswith("--"):
            cursor += 1

        if cursor >= len(tokens) or tokens[cursor] != "push":
            continue

        for arg in tokens[cursor + 1 :]:
            if arg in SHELL_OPERATORS:
                break
            if arg in {"-f", "--force", "--force-with-lease"}:
                return True
            if arg.startswith("--force-with-lease="):
                return True
            if arg.startswith("+") and ":" in arg:
                return True

    return False


def delete_without_where(sql: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement_tail = sql[match.end() :]
        statement_tail = statement_tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement_tail, flags=re.IGNORECASE):
            return True
    return False


def destructive_sql_reason(sql: str) -> str | None:
    sql = normalize_sql(sql)
    if re.search(r"\bdrop\s+table\b", sql, flags=re.IGNORECASE):
        return "DROP TABLE can permanently remove a database table."
    if re.search(r"\btruncate(?:\s+table)?\b", sql, flags=re.IGNORECASE):
        return "TRUNCATE can remove all rows from a table."
    if delete_without_where(sql):
        return "DELETE FROM without a WHERE clause can remove every row."
    return None


def has_destructive_sql(tokens: list[str]) -> str | None:
    segments = command_segments(tokens)

    if any(command_name(segment) in DATABASE_CLIENTS for segment in segments):
        reason = destructive_sql_reason(" ".join(tokens))
        if reason:
            return reason

    for segment in segments:
        name = command_name(segment)
        if name in SAFE_TEXT_COMMANDS:
            continue

        reason = destructive_sql_reason(" ".join(segment))
        if reason:
            return reason

    return None


def nested_shell_commands(tokens: list[str]) -> list[str]:
    nested: list[str] = []
    for index, token in enumerate(tokens):
        if Path(token).name not in SHELL_WORDS:
            continue
        for offset, arg in enumerate(tokens[index + 1 :], start=index + 1):
            if arg == "-c" and offset + 1 < len(tokens):
                nested.append(tokens[offset + 1])
                break
    return nested


def find_block_reason(command: str, depth: int = 0) -> str | None:
    if depth > 4:
        return None

    try:
        tokens = split_command(command)
    except ValueError:
        tokens = command.split()

    if has_recursive_force_rm(tokens):
        return "rm with both recursive and force flags can irreversibly delete files."
    if has_forced_git_push(tokens):
        return "Forced git pushes can overwrite remote history."

    sql_reason = has_destructive_sql(tokens)
    if sql_reason:
        return sql_reason

    for nested in nested_shell_commands(tokens):
        nested_reason = find_block_reason(nested, depth + 1)
        if nested_reason:
            return nested_reason

    return None


def log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": payload.get("cwd") or os.getcwd(),
        "command": command,
        "reason": reason,
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError:
        pass


def deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(response))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    log_block(payload, command, reason)
    deny(f"Destructive Bash command blocked: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
