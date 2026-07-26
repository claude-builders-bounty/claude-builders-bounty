#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import shlex
import sys
from typing import Iterable


SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "duckdb"}
WRAPPERS = {"command", "builtin", "nohup"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def command_name(value: str) -> str:
    """Return a lower-case executable basename for POSIX or Windows paths."""
    return value.replace("\\", "/").rsplit("/", 1)[-1].lower()


def parse_shell(command: str) -> tuple[list[list[str]], list[str]]:
    """Tokenize simple commands and retain their separating shell operators."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = "#"
        tokens = list(lexer)
    except ValueError:
        return [], []

    commands: list[list[str]] = []
    operators: list[str] = []
    current: list[str] = []
    for token in tokens:
        if token and all(character in ";&|" for character in token):
            if current:
                commands.append(current)
                current = []
                operators.append(token)
            elif operators:
                operators[-1] += token
        else:
            current.append(token)
    if current:
        commands.append(current)
    if len(operators) >= len(commands):
        operators = operators[: max(0, len(commands) - 1)]
    return commands, operators


def unwrap_command(tokens: list[str]) -> tuple[str, list[str]]:
    """Return the executable and arguments after common shell wrappers."""
    index = 0
    while index < len(tokens) and ASSIGNMENT.match(tokens[index]):
        index += 1
    if index >= len(tokens):
        return "", []

    name = command_name(tokens[index])
    index += 1

    if name == "sudo":
        options_with_values = {
            "-u", "--user", "-g", "--group", "-h", "--host",
            "-p", "--prompt", "-C", "--close-from", "-R", "--chroot",
            "-T", "--command-timeout",
        }
        while index < len(tokens) and tokens[index].startswith("-"):
            option = tokens[index]
            index += 1
            if option == "--":
                break
            if option in options_with_values and index < len(tokens):
                index += 1
        if index >= len(tokens):
            return "", []
        name = command_name(tokens[index])
        index += 1

    if name == "env":
        while index < len(tokens):
            token = tokens[index]
            if token == "--":
                index += 1
                break
            if token.startswith("-") or ASSIGNMENT.match(token):
                index += 1
                continue
            break
        if index >= len(tokens):
            return "", []
        name = command_name(tokens[index])
        index += 1

    while name in WRAPPERS and index < len(tokens):
        name = command_name(tokens[index])
        index += 1

    return name, tokens[index:]


def has_recursive_force_rm(arguments: Iterable[str]) -> bool:
    """Return true when rm options include both recursive and force."""
    recursive = False
    force = False
    for argument in arguments:
        if argument == "--":
            break
        if argument == "--recursive":
            recursive = True
        elif argument == "--force":
            force = True
        elif argument.startswith("--"):
            continue
        elif argument.startswith("-") and argument != "-":
            flags = argument[1:].lower()
            recursive = recursive or "r" in flags
            force = force or "f" in flags
    return recursive and force


def is_forced_git_push(arguments: list[str]) -> bool:
    """Recognize a git push subcommand with an exact force option."""
    index = 0
    options_with_values = {
        "-C", "-c", "--git-dir", "--work-tree", "--namespace",
        "--super-prefix", "--config-env",
    }
    while index < len(arguments) and arguments[index].startswith("-"):
        option = arguments[index]
        index += 1
        if option in options_with_values and index < len(arguments):
            index += 1
    if index >= len(arguments) or arguments[index].lower() != "push":
        return False
    return any(
        argument in {"-f", "--force"} or argument.startswith("--force=")
        for argument in arguments[index + 1 :]
    )


def strip_sql_comments_and_literals(sql: str) -> str:
    """Mask SQL comments and single-quoted string literals."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\r\n]*", " ", sql)

    output: list[str] = []
    index = 0
    in_string = False
    while index < len(sql):
        character = sql[index]
        if not in_string:
            if character == "'":
                in_string = True
                output.append(" ")
            else:
                output.append(character)
            index += 1
            continue

        if character == "'" and index + 1 < len(sql) and sql[index + 1] == "'":
            output.extend((" ", " "))
            index += 2
        elif character == "'":
            in_string = False
            output.append(" ")
            index += 1
        else:
            output.append(" ")
            index += 1

    return "".join(output)


def sql_reason(sql: str) -> str | None:
    """Return a block reason for destructive SQL, statement by statement."""
    cleaned = strip_sql_comments_and_literals(sql)
    for statement in cleaned.split(";"):
        if DROP_TABLE.search(statement):
            return "DROP TABLE can destroy database data"
        if TRUNCATE.search(statement):
            return "TRUNCATE can destroy database data"
        for match in DELETE_FROM.finditer(statement):
            if not WHERE.search(statement[match.end() :]):
                return "DELETE FROM without a WHERE clause can delete every row"
    return None


def nested_shell_text(arguments: list[str]) -> str | None:
    for index, argument in enumerate(arguments):
        if argument == "-c" and index + 1 < len(arguments):
            return arguments[index + 1]
        if argument.startswith("-") and "c" in argument[1:] and index + 1 < len(arguments):
            return arguments[index + 1]
    return None


def sql_arguments(name: str, arguments: list[str], tokens: list[str]) -> list[str]:
    """Extract SQL supplied directly to a known client or SQL verb."""
    if name in {"drop", "truncate", "delete"}:
        return [" ".join(tokens)]
    if name not in SQL_CLIENTS:
        return []

    values: list[str] = []
    separated_options = {"-c", "--command", "-e", "--execute", "-Q", "--query"}
    long_prefixes = ("--command=", "--execute=", "--query=")
    short_prefixes = ("-c", "-e", "-Q")

    index = 0
    while index < len(arguments):
        argument = arguments[index]

        if argument in separated_options:
            if index + 1 < len(arguments):
                values.append(arguments[index + 1])
                index += 2
                continue
            break

        matched = False
        for prefix in long_prefixes:
            if argument.startswith(prefix):
                value = argument[len(prefix) :]
                if value:
                    values.append(value)
                matched = True
                break
        if matched:
            index += 1
            continue

        for prefix in short_prefixes:
            if argument.startswith(prefix) and argument != prefix:
                value = argument[len(prefix) :]
                if value:
                    values.append(value)
                matched = True
                break
        index += 1

    if name == "sqlite3":
        option_values = {
            "-cmd",
            "-init",
            "-separator",
            "-newline",
            "-nullvalue",
            "-vfs",
            "-vfstrace",
        }
        positionals: list[str] = []
        index = 0
        while index < len(arguments):
            argument = arguments[index]
            if argument == "--":
                positionals.extend(arguments[index + 1 :])
                break
            if argument in option_values:
                index += 2
                continue
            if argument.startswith("-"):
                index += 1
                continue
            positionals.append(argument)
            index += 1

        # sqlite3 syntax is: sqlite3 [options] [database [SQL]]
        if len(positionals) >= 2:
            values.append(" ".join(positionals[1:]))

    return values


def literal_producer_output(name: str, arguments: list[str]) -> str | None:
    """Infer literal output for simple echo/printf pipeline producers."""
    if name == "echo":
        index = 0
        while index < len(arguments) and arguments[index] in {"-n", "-e", "-E"}:
            index += 1
        return " ".join(arguments[index:])

    if name == "printf" and arguments:
        format_text = arguments[0]
        if len(arguments) == 1:
            return format_text
        try:
            return format_text % tuple(arguments[1:])
        except (TypeError, ValueError):
            return format_text + " " + " ".join(arguments[1:])

    return None


def piped_sql_reason(
    commands: list[list[str]],
    operators: list[str],
) -> str | None:
    """Inspect literal echo/printf data piped directly into an SQL client."""
    for index, operator in enumerate(operators):
        if operator != "|" or index + 1 >= len(commands):
            continue
        producer_name, producer_arguments = unwrap_command(commands[index])
        consumer_name, consumer_arguments = unwrap_command(commands[index + 1])
        if consumer_name not in SQL_CLIENTS:
            continue
        if sql_arguments(consumer_name, consumer_arguments, commands[index + 1]):
            continue
        payload = literal_producer_output(producer_name, producer_arguments)
        if payload is None:
            continue
        reason = sql_reason(payload)
        if reason:
            return reason
    return None


def blocked_reason(command: str, *, _depth: int = 0) -> str | None:
    """Classify executable commands without scanning harmless quoted text."""
    if _depth > 2:
        return None

    commands, operators = parse_shell(command)
    reason = piped_sql_reason(commands, operators)
    if reason:
        return reason

    for tokens in commands:
        name, arguments = unwrap_command(tokens)
        if not name:
            continue

        if name == "rm" and has_recursive_force_rm(arguments):
            return "recursive forced file deletion"

        if name == "git" and is_forced_git_push(arguments):
            return "a forced Git push can overwrite remote history"

        if name in SHELLS:
            nested = nested_shell_text(arguments)
            if nested:
                reason = blocked_reason(nested, _depth=_depth + 1)
                if reason:
                    return reason

        for sql in sql_arguments(name, arguments, tokens):
            reason = sql_reason(sql)
            if reason:
                return reason

    return None


def log_blocked(command: str, project_path: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as log:
        json.dump(record, log, ensure_ascii=False)
        log.write("\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = payload.get("cwd")
    if not isinstance(project_path, str):
        project_path = os.getcwd()
    log_blocked(command, project_path)
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Command blocked: {reason}.",
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
