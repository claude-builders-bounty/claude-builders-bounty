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


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
SQL_CLIENTS = {
    "clickhouse-client",
    "cockroach",
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite3",
    "sqlcmd",
}
COMMAND_WRAPPERS = {"builtin", "command", "nohup", "sudo", "time"}
SHELL_SEPARATORS = {";", "&&", "||", "|"}
SUDO_OPTIONS_WITH_VALUES = {
    "-C",
    "--chdir",
    "-g",
    "--group",
    "-h",
    "--host",
    "-p",
    "--prompt",
    "-R",
    "--chroot",
    "-T",
    "--command-timeout",
    "-u",
    "--user",
}
ENV_OPTIONS_WITH_VALUES = {"-C", "--chdir", "-S", "--split-string", "-u", "--unset"}
GIT_OPTIONS_WITH_VALUES = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}


def find_block_reason(command: str) -> str | None:
    if _contains_forced_recursive_rm(command):
        return "Blocked destructive recursive remove command (rm with recursive and force flags)."

    if _contains_git_force_push(command):
        return "Blocked force-push command. Use a reviewed non-force push workflow instead."

    if _contains_sql_pattern(command, r"\bdrop\s+table\b"):
        return "Blocked SQL DROP TABLE statement."

    if _contains_sql_pattern(command, r"\btruncate\b"):
        return "Blocked SQL TRUNCATE statement."

    if _contains_delete_without_where(command):
        return "Blocked SQL DELETE FROM statement without a WHERE clause."

    return None


def build_denial(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def log_block(input_data: dict[str, Any], command: str, reason: str) -> None:
    project_path = input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    if not isinstance(input_data, dict) or input_data.get("tool_name") != "Bash":
        return 0

    tool_input = input_data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    log_block(input_data, command, reason)
    print(json.dumps(build_denial(reason)))
    return 0


def _contains_forced_recursive_rm(command: str) -> bool:
    for argv in _simple_commands(command):
        rm_index = _executable_index(argv, "rm")
        if rm_index is None:
            continue

        flags = argv[rm_index + 1 :]
        has_recursive = False
        has_force = False
        for flag in flags:
            if flag == "--":
                break
            if flag in {"-r", "-R", "--recursive"}:
                has_recursive = True
            if flag in {"-f", "--force"}:
                has_force = True
            if flag.startswith("-") and not flag.startswith("--"):
                has_recursive = has_recursive or "r" in flag.lower()
                has_force = has_force or "f" in flag.lower()

        if has_recursive and has_force:
            return True

    return False


def _contains_git_force_push(command: str) -> bool:
    for argv in _simple_commands(command):
        git_index = _executable_index(argv, "git")
        if git_index is None:
            continue
        push_index = _git_subcommand_index(argv, git_index)
        if push_index is None or argv[push_index] != "push":
            continue
        push_args = argv[push_index + 1 :]
        if any(arg in {"--force", "-f", "--force-with-lease"} for arg in push_args):
            return True
        if any(arg.startswith("+") and len(arg) > 1 for arg in push_args if not arg.startswith("++")):
            return True
    return False


def _contains_sql_pattern(command: str, pattern: str) -> bool:
    for statement in _sql_statements(command):
        if re.search(pattern, statement, flags=re.IGNORECASE):
            return True
    return False


def _contains_delete_without_where(command: str) -> bool:
    for statement in _sql_statements(command):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b",
            statement,
            flags=re.IGNORECASE,
        ):
            return True
    return False


def _sql_statements(command: str) -> list[str]:
    statements: list[str] = []
    for group in _pipeline_groups(command):
        if not group:
            continue
        rendered = " ".join(group)
        if _group_uses_sql_client(group) or _starts_with_sql_keyword(rendered):
            statements.extend(part.strip() for part in rendered.split(";") if part.strip())
    return statements


def _group_uses_sql_client(group: list[str]) -> bool:
    current: list[str] = []
    for token in [*group, "|"]:
        if token == "|":
            if current and any(_executable_index(current, client) is not None for client in SQL_CLIENTS):
                return True
            current = []
        else:
            current.append(token)
    return False


def _starts_with_sql_keyword(statement: str) -> bool:
    return bool(re.match(r"^\s*(drop\s+table|truncate|delete\s+from)\b", statement, flags=re.IGNORECASE))


def _simple_commands(command: str) -> list[list[str]]:
    commands: list[list[str]] = []
    for group in _token_groups(command):
        current: list[str] = []
        for token in [*group, "|"]:
            if token == "|":
                if current:
                    commands.append(current)
                current = []
            else:
                current.append(token)
    return commands


def _pipeline_groups(command: str) -> list[list[str]]:
    return _token_groups(command)


def _token_groups(command: str) -> list[list[str]]:
    groups: list[list[str]] = []
    for line in command.splitlines() or [command]:
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lexer.whitespace_split = True
            lexer.commenters = ""
            tokens = list(lexer)
        except ValueError:
            tokens = line.split()

        current: list[str] = []
        for token in tokens:
            if token in {";", "&&", "||"}:
                if current:
                    groups.append(current)
                current = []
                continue
            if token and set(token) <= set(";&|") and token not in SHELL_SEPARATORS:
                if current:
                    groups.append(current)
                current = []
                continue
            current.append(token)
        if current:
            groups.append(current)
    return groups


def _executable_index(argv: list[str], name: str) -> int | None:
    if not argv:
        return None

    index = 0
    while index < len(argv):
        token = argv[index]
        if _is_command_name(token, name):
            return index

        base = Path(token).name
        if base == "env":
            index = _skip_wrapper_options(argv, index + 1, ENV_OPTIONS_WITH_VALUES, allow_assignments=True)
            continue

        if base == "sudo":
            index = _skip_wrapper_options(argv, index + 1, SUDO_OPTIONS_WITH_VALUES, allow_assignments=True)
            continue

        if base in COMMAND_WRAPPERS:
            index += 1
            while index < len(argv) and argv[index].startswith("-"):
                index += 1
            continue

        return None

    return None


def _skip_wrapper_options(
    argv: list[str],
    index: int,
    options_with_values: set[str],
    *,
    allow_assignments: bool,
) -> int:
    while index < len(argv):
        token = argv[index]
        if token == "--":
            return index + 1
        if allow_assignments and "=" in token and not token.startswith("=") and not token.startswith("-"):
            index += 1
            continue
        if token in options_with_values:
            index += 2
            continue
        if any(token.startswith(f"{option}=") for option in options_with_values if option.startswith("--")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return index
    return index


def _git_subcommand_index(argv: list[str], git_index: int) -> int | None:
    index = git_index + 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            index += 1
            break
        if token in GIT_OPTIONS_WITH_VALUES:
            index += 2
            continue
        if any(token.startswith(f"{option}=") for option in GIT_OPTIONS_WITH_VALUES if option.startswith("--")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        break
    return index if index < len(argv) else None


def _is_command_name(arg: str, name: str) -> bool:
    return arg == name or arg.endswith(f"/{name}")


if __name__ == "__main__":
    raise SystemExit(main())
