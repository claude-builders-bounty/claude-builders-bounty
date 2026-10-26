#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


SQL_CLIENTS = {
    "psql",
    "mysql",
    "mariadb",
    "sqlite3",
    "sqlcmd",
    "duckdb",
}

SQL_PATTERNS = {
    "drop table": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    "truncate": re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
}

DELETE_PATTERN = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_PATTERN = re.compile(r"\bWHERE\b", re.IGNORECASE)

VIEWER_COMMANDS = {
    "cat",
    "echo",
    "printf",
    "grep",
    "rg",
    "awk",
    "sed",
    "jq",
    "yq",
    "find",
    "ls",
    "history",
}

COMMAND_WRAPPERS = {
    "command",
    "env",
    "nice",
    "nohup",
    "sudo",
}

SHELL_COMMANDS = {
    "bash",
    "sh",
    "zsh",
}


def hook_output(decision: str, reason: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }
    )


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        raise


def command_segments(tokens: list[str]) -> list[list[str]]:
    segment: list[str] = []
    segments: list[list[str]] = []

    for token in tokens:
        if token in {";", "|", "||", "&&", "&", "\n"}:
            if segment:
                segments.append(segment)
            segment = []
        else:
            segment.append(token)

    if segment:
        segments.append(segment)
    return segments


def rm_flags(segment: list[str], start: int) -> tuple[bool, bool]:
    recursive = False
    force = False
    reached_end_of_options = False

    for token in segment[start + 1 :]:
        if token in {";", "|", "||", "&&", "&", "\n"}:
            break
        if reached_end_of_options or not token.startswith("-"):
            continue
        if token == "--":
            reached_end_of_options = True
            continue
        if token.startswith("--"):
            force = force or token == "--force"
            recursive = recursive or token == "--recursive"
            continue
        force = force or "f" in token[1:]
        recursive = recursive or any(character in token[1:] for character in "rR")

    return recursive, force


def find_rm_risk(segment: list[str]) -> str | None:
    index = 0
    while index < len(segment):
        token = segment[index]
        if token == "env" and index + 1 < len(segment) and "=" in segment[index + 1]:
            index += 1
            continue
        if token not in COMMAND_WRAPPERS:
            if token == "rm" or token.endswith("/rm"):
                recursive, force = rm_flags(segment, index)
                if recursive and force:
                    return "rm was called with both recursive and force flags"
            break
        index += 1
    return None


def find_git_push_force(segment: list[str]) -> str | None:
    index = 0
    while index < len(segment) - 1:
        if segment[index] != "git":
            index += 1
            continue
        position = index + 1
        while position < len(segment) and segment[position].startswith("-"):
            position += 1
        if position >= len(segment):
            return None
        if segment[position] != "push":
            return None

        reached_end_of_options = False
        for token in segment[position + 1 :]:
            if token in {";", "|", "||", "&&", "&", "\n"}:
                break
            if reached_end_of_options or not token.startswith("-"):
                continue
            if token == "--":
                reached_end_of_options = True
                continue
            if token == "--force" or token[1:] == "f":
                return "git push would overwrite the remote branch with --force or -f"
        return None
    return None


def sql_statements(text: str) -> list[str]:
    return [statement.strip() for statement in re.split(r"[;\n]+", text) if statement.strip()]


def sql_risk(text: str) -> str | None:
    for pattern_name, pattern in SQL_PATTERNS.items():
        if pattern.search(text):
            return f"the SQL command contains a destructive {pattern_name.upper()} statement"

    for statement in sql_statements(text):
        if DELETE_PATTERN.search(statement) and not WHERE_PATTERN.search(statement):
            return "the SQL DELETE statement has no WHERE clause"

    return None


def segment_risk(segment: list[str]) -> str | None:
    risk = find_rm_risk(segment)
    if risk:
        return risk

    risk = find_git_push_force(segment)
    if risk:
        return risk

    if segment and segment[0] in VIEWER_COMMANDS:
        return None

    if segment and segment[0] in SHELL_COMMANDS:
        for index, token in enumerate(segment):
            if token == "-c" and index + 1 < len(segment):
                return inspect_command(segment[index + 1])

    command_text = " ".join(segment)
    has_sql_client = any(client in segment for client in SQL_CLIENTS)
    has_nested_sql_client = any(client in command_text for client in SQL_CLIENTS)
    if has_sql_client or has_nested_sql_client:
        return sql_risk(command_text)

    return None


def inspect_command(command: str) -> str | None:
    try:
        tokens = tokenize(command)
    except ValueError as error:
        return f"the command could not be parsed safely: {error}"

    for segment in command_segments(tokens):
        risk = segment_risk(segment)
        if risk:
            return risk
    return None


def log_block(command: str, project_path: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run(input_data: dict[str, object]) -> str | None:
    if input_data.get("tool_name") != "Bash":
        return None

    tool_input = input_data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        return None

    reason = inspect_command(command)
    if reason:
        project_path = str(input_data.get("cwd") or os.environ.get("PWD") or "unknown")
        log_block(command, project_path)
        return hook_output(
            "deny",
            f"Blocked because {reason}. Revise the command so it cannot destroy data or overwrite history.",
        )
    return None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0

    if not isinstance(input_data, dict):
        return 0

    try:
        output = run(input_data)
    except OSError as error:
        print(f"destructive-bash-guard could not inspect input: {error}", file=sys.stderr)
        return 0

    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
