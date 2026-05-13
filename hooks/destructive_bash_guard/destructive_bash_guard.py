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
from typing import Iterable, Sequence


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
CONTROL_TOKENS = {";", ";;", "&&", "||", "|", "|&", "\n"}
WRAPPER_COMMANDS = {"command", "builtin", "noglob", "time"}
DB_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "duckdb", "sqlcmd"}
SQL_COMMENT_RE = re.compile(r"(--[^\n\r]*|/\*.*?\*/)", re.IGNORECASE | re.DOTALL)
SQL_DIRECT_RE = re.compile(r"^\s*(?:DROP\s+(?:TEMPORARY\s+)?TABLE|TRUNCATE|DELETE\s+FROM)\b", re.IGNORECASE)
DROP_TABLE_RE = re.compile(r"\bDROP\s+(?:TEMPORARY\s+)?TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[A-Za-z_][\w.$`\"-]*", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)


class BlockedCommand(Exception):
    """Raised when a command matches a destructive pattern."""

    def __init__(self, rule: str, reason: str) -> None:
        self.rule = rule
        self.reason = reason
        super().__init__(reason)


def tokenize_shell(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def split_simple_commands(tokens: Iterable[str]) -> Iterable[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in CONTROL_TOKENS:
            if current:
                yield current
                current = []
            continue
        current.append(token)
    if current:
        yield current


def clean_command_name(token: str) -> str:
    token = token.lstrip("\\")
    return Path(token).name


def is_assignment(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token))


def strip_leading_wrappers(tokens: Sequence[str]) -> list[str]:
    remaining = list(tokens)

    while remaining:
        name = clean_command_name(remaining[0])

        if is_assignment(remaining[0]):
            remaining.pop(0)
            continue

        if name in WRAPPER_COMMANDS:
            remaining.pop(0)
            continue

        if name == "sudo" or name == "doas":
            remaining.pop(0)
            while remaining and remaining[0].startswith("-"):
                option = remaining.pop(0)
                if option in {"-u", "-g", "-h", "-p", "-C", "-T"} and remaining:
                    remaining.pop(0)
            continue

        if name == "env":
            remaining.pop(0)
            while remaining and (remaining[0].startswith("-") or is_assignment(remaining[0])):
                remaining.pop(0)
            continue

        return remaining

    return remaining


def short_option_has(option: str, flag: str) -> bool:
    return option.startswith("-") and not option.startswith("--") and flag.lower() in option[1:].lower()


def inspect_rm(tokens: Sequence[str]) -> None:
    command = strip_leading_wrappers(tokens)
    if not command or clean_command_name(command[0]) != "rm":
        return

    recursive = False
    force = False
    for token in command[1:]:
        if token == "--":
            break
        if not token.startswith("-"):
            continue
        recursive = recursive or token in {"-r", "-R", "--recursive"} or short_option_has(token, "r")
        force = force or token in {"-f", "--force"} or short_option_has(token, "f")

    if recursive and force:
        raise BlockedCommand(
            "rm-recursive-force",
            "Blocked rm with both recursive and force flags. Use a safer cleanup command or remove files explicitly.",
        )


def inspect_git_push(tokens: Sequence[str]) -> None:
    command = strip_leading_wrappers(tokens)
    if not command or clean_command_name(command[0]) != "git":
        return

    try:
        push_index = command.index("push")
    except ValueError:
        return

    for token in command[push_index + 1 :]:
        if token == "--force" or token.startswith("--force=") or short_option_has(token, "f"):
            raise BlockedCommand(
                "git-push-force",
                "Blocked git push with force. Use --force-with-lease only after confirming remote history is safe to replace.",
            )


def stripped_sql(command: str) -> str:
    return SQL_COMMENT_RE.sub("", command)


def inspect_sql(command: str) -> None:
    sql = stripped_sql(command)

    if DROP_TABLE_RE.search(sql):
        raise BlockedCommand("drop-table", "Blocked DROP TABLE because it can permanently destroy schema and data.")

    if TRUNCATE_RE.search(sql):
        raise BlockedCommand("truncate", "Blocked TRUNCATE because it removes all rows from a table.")

    for match in DELETE_FROM_RE.finditer(sql):
        statement_end = sql.find(";", match.end())
        if statement_end == -1:
            statement_end = len(sql)
        statement = sql[match.start() : statement_end]
        if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
            raise BlockedCommand(
                "delete-without-where",
                "Blocked DELETE FROM without a WHERE clause because it can remove every row.",
            )


def should_scan_sql(command: str, tokens: Sequence[str]) -> bool:
    if SQL_DIRECT_RE.search(stripped_sql(command)):
        return True

    for simple_command in split_simple_commands(tokens):
        command_tokens = strip_leading_wrappers(simple_command)
        if command_tokens and clean_command_name(command_tokens[0]).lower() in DB_CLIENTS:
            return True

    return False


def inspect_command(command: str) -> None:
    try:
        tokens = tokenize_shell(command)
    except ValueError:
        tokens = []

    if not tokens:
        inspect_sql(command)
        if re.search(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-[A-Za-z]*f[A-Za-z]*r)", command, re.IGNORECASE):
            raise BlockedCommand(
                "rm-recursive-force",
                "Blocked rm with recursive and force flags in an unparsable shell command.",
            )
        return

    if should_scan_sql(command, tokens):
        inspect_sql(command)

    for simple_command in split_simple_commands(tokens):
        inspect_rm(simple_command)
        inspect_git_push(simple_command)


def log_blocked(command: str, rule: str, reason: str, project_path: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "rule": rule,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload))


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if hook_input.get("tool_name") != "Bash":
        return 0

    command = str(hook_input.get("tool_input", {}).get("command", ""))
    if not command.strip():
        return 0

    project_path = str(hook_input.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())

    try:
        inspect_command(command)
    except BlockedCommand as blocked:
        try:
            log_blocked(command, blocked.rule, blocked.reason, project_path)
        finally:
            deny(blocked.reason)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
