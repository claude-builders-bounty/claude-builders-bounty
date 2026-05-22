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


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
SEGMENT_SEPARATORS = {";", "&&", "||", "|"}
SUDO_OPTIONS_WITH_VALUES = {
    "-A",
    "-C",
    "-D",
    "-g",
    "-h",
    "-p",
    "-R",
    "-r",
    "-T",
    "-t",
    "-U",
    "-u",
}
GIT_OPTIONS_WITH_VALUES = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
}


def main() -> int:
    payload = read_payload()
    command = extract_bash_command(payload)
    if not command:
        return 0

    reason = detect_danger(command)
    if not reason:
        return 0

    project_path = payload.get("cwd") or os.getenv("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_error = log_blocked_attempt(command, str(project_path), reason)
    print_block_decision(reason, log_error)
    return 0


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def extract_bash_command(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def detect_danger(command: str) -> str | None:
    sql_reason = detect_dangerous_sql(command)
    if sql_reason:
        return sql_reason

    for segment in command_segments(command):
        normalized = strip_command_wrappers(segment)
        if not normalized:
            continue

        rm_reason = detect_rm_rf(normalized)
        if rm_reason:
            return rm_reason

        git_reason = detect_force_push(normalized)
        if git_reason:
            return git_reason

    return None


def command_segments(command: str) -> Iterable[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return fallback_segments(command)

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SEGMENT_SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)

    if current:
        segments.append(current)

    return segments


def fallback_segments(command: str) -> list[list[str]]:
    chunks = re.split(r"(?:&&|\|\||[;|\n])", command)
    return [chunk.split() for chunk in chunks if chunk.strip()]


def strip_command_wrappers(segment: Sequence[str]) -> list[str]:
    tokens = list(segment)
    while tokens and ASSIGNMENT_RE.match(tokens[0]):
        tokens.pop(0)

    while tokens:
        command = command_name(tokens[0])

        if command in {"command", "builtin", "time"}:
            tokens.pop(0)
            continue

        if command == "sudo":
            tokens.pop(0)
            tokens = strip_sudo_options(tokens)
            continue

        if command == "env":
            tokens.pop(0)
            tokens = strip_env_prefix(tokens)
            continue

        break

    return tokens


def strip_sudo_options(tokens: list[str]) -> list[str]:
    output = list(tokens)
    while output and output[0].startswith("-"):
        option = output.pop(0)
        if option in SUDO_OPTIONS_WITH_VALUES and output:
            output.pop(0)
    return output


def strip_env_prefix(tokens: list[str]) -> list[str]:
    output = list(tokens)
    while output:
        token = output[0]
        if ASSIGNMENT_RE.match(token):
            output.pop(0)
            continue
        if token.startswith("-"):
            output.pop(0)
            continue
        break
    return output


def command_name(token: str) -> str:
    return token.replace("\\", "/").rstrip("/").split("/")[-1]


def detect_rm_rf(tokens: Sequence[str]) -> str | None:
    if command_name(tokens[0]) != "rm":
        return None

    recursive = False
    force = False
    for token in tokens[1:]:
        if token == "--":
            break
        if token == "--recursive":
            recursive = True
        elif token == "--force":
            force = True
        elif token.startswith("-") and not token.startswith("--"):
            flags = token.lstrip("-")
            recursive = recursive or "r" in flags or "R" in flags
            force = force or "f" in flags

    if recursive and force:
        return "rm with both recursive and force flags is blocked"
    return None


def detect_force_push(tokens: Sequence[str]) -> str | None:
    if command_name(tokens[0]) != "git":
        return None

    index = first_git_subcommand_index(tokens)
    if index is None or index >= len(tokens) or tokens[index] != "push":
        return None

    force_flags = {"-f", "--force"}
    for token in tokens[index + 1 :]:
        if token in force_flags or token.startswith("--force-with-lease"):
            return "force-pushing with git push is blocked"

    return None


def first_git_subcommand_index(tokens: Sequence[str]) -> int | None:
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token in GIT_OPTIONS_WITH_VALUES:
            index += 2
            continue
        if any(token.startswith(option + "=") for option in GIT_OPTIONS_WITH_VALUES):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return index
    return None


def detect_dangerous_sql(command: str) -> str | None:
    if DROP_TABLE_RE.search(command):
        return "DROP TABLE statements are blocked"

    if TRUNCATE_RE.search(command):
        return "TRUNCATE statements are blocked"

    for statement in split_sql_statements(command):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "DELETE FROM without a WHERE clause is blocked"

    return None


def split_sql_statements(command: str) -> Iterable[str]:
    return re.split(r";|\n", command)


def log_blocked_attempt(command: str, project_path: str, reason: str) -> str | None:
    log_path = Path(
        os.getenv("CLAUDE_BLOCKED_LOG", "~/.claude/hooks/blocked.log")
    ).expanduser()
    entry = {
        "timestamp": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError as exc:
        return f"Blocked attempt could not be written to {log_path}: {exc}"
    return None


def print_block_decision(reason: str, log_error: str | None) -> None:
    message = (
        f"{reason}. Rewrite the operation with a safer command or ask the "
        "user for an explicit manual override."
    )
    if log_error:
        message = f"{message} {log_error}"

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(response, separators=(",", ":")))


if __name__ == "__main__":
    raise SystemExit(main())
