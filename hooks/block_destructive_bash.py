#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
import re
import shlex
import sys
from typing import Iterable


HOOK_EVENT_NAME = "PreToolUse"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

SQL_CLIENTS = {
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite3",
    "sqlcmd",
}

SQL_CLIENT_RE = re.compile(
    r"(?i)(?:^|[;&|()\s])(?:duckdb|mariadb|mysql|psql|sqlite3|sqlcmd)\b"
)
DIRECT_SQL_RE = re.compile(r"(?is)^\s*(?:drop\s+table|truncate\b|delete\s+from)\b")


def split_shell_segments(command: str) -> list[str]:
    """Split a shell command on common command separators while respecting quotes."""
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    i = 0

    while i < len(command):
        char = command[i]
        next_char = command[i + 1] if i + 1 < len(command) else ""

        if escaped:
            current.append(char)
            escaped = False
            i += 1
            continue

        if char == "\\" and quote != "'":
            current.append(char)
            escaped = True
            i += 1
            continue

        if quote:
            current.append(char)
            if char == quote:
                quote = None
            i += 1
            continue

        if char in ("'", '"'):
            quote = char
            current.append(char)
            i += 1
            continue

        if char in (";", "\n") or (char in ("&", "|") and next_char == char) or char == "|":
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
            i += 2 if char in ("&", "|") and next_char == char else 1
            continue

        current.append(char)
        i += 1

    segment = "".join(current).strip()
    if segment:
        segments.append(segment)
    return segments


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return []


def base_command(token: str) -> str:
    return Path(token).name.lower()


def command_start(tokens: list[str]) -> int | None:
    """Return the index of the real command after env vars and simple wrappers."""
    index = 0
    while index < len(tokens):
        token = tokens[index]
        name = base_command(token)

        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token):
            index += 1
            continue

        if name == "sudo":
            index += 1
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 1
            continue

        if name == "command":
            index += 1
            continue

        if name == "env":
            index += 1
            while index < len(tokens):
                if tokens[index].startswith("-") or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[index]):
                    index += 1
                    continue
                break
            continue

        return index

    return None


def option_has_short(option: str, flag: str) -> bool:
    return option.startswith("-") and not option.startswith("--") and flag in option[1:]


def contains_rm_rf(tokens: list[str]) -> bool:
    start = command_start(tokens)
    if start is None or base_command(tokens[start]) != "rm":
        return False

    recursive = False
    force = False
    for token in tokens[start + 1 :]:
        if token == "--":
            break
        if not token.startswith("-"):
            continue
        if token == "--recursive" or option_has_short(token, "r") or option_has_short(token, "R"):
            recursive = True
        if token == "--force" or option_has_short(token, "f"):
            force = True
        if recursive and force:
            return True

    return False


def contains_force_push(tokens: list[str]) -> bool:
    start = command_start(tokens)
    if start is None or base_command(tokens[start]) != "git":
        return False

    index = start + 1
    while index < len(tokens):
        token = tokens[index]
        if token == "push":
            break
        if token in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            index += 2
            continue
        if token.startswith(("-C", "-c", "--git-dir=", "--work-tree=", "--namespace=")):
            index += 1
            continue
        index += 1
    else:
        return False

    for token in tokens[index + 1 :]:
        if token == "--":
            break
        if token == "--force" or token.startswith("--force=") or token.startswith("--force-"):
            return True
        if option_has_short(token, "f"):
            return True
    return False


def nested_shell_commands(tokens: list[str]) -> Iterable[str]:
    start = command_start(tokens)
    if start is None or base_command(tokens[start]) not in {"bash", "sh", "zsh"}:
        return ()

    nested: list[str] = []
    index = start + 1
    while index < len(tokens):
        token = tokens[index]
        if token == "-c" and index + 1 < len(tokens):
            nested.append(tokens[index + 1])
            index += 2
            continue
        if token.startswith("-c") and len(token) > 2:
            nested.append(token[2:])
        index += 1
    return nested


def sql_text_for_command(command: str) -> str:
    parts: list[str] = []
    for segment in split_shell_segments(command):
        tokens = tokenize(segment)
        parts.append(" ".join(tokens) if tokens else segment)
    return "\n".join(parts)


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"(?s)/\*.*?\*/", " ", sql)
    sql = re.sub(r"(?m)--[^\n]*", " ", sql)
    return sql


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    single_quote = False
    i = 0

    while i < len(sql):
        char = sql[i]
        if char == "'":
            current.append(char)
            if single_quote and i + 1 < len(sql) and sql[i + 1] == "'":
                current.append(sql[i + 1])
                i += 2
                continue
            single_quote = not single_quote
            i += 1
            continue
        if char == ";" and not single_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue
        current.append(char)
        i += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements


def delete_without_where(sql: str) -> bool:
    for statement in split_sql_statements(strip_sql_comments(sql)):
        match = re.search(r"(?is)\bdelete\s+from\b", statement)
        if match and not re.search(r"(?is)\bwhere\b", statement[match.end() :]):
            return True
    return False


def sql_context(command: str, sql_text: str) -> bool:
    return bool(SQL_CLIENT_RE.search(command) or DIRECT_SQL_RE.search(sql_text))


def detect_dangers(command: str) -> list[str]:
    reasons: list[str] = []

    for segment in split_shell_segments(command):
        tokens = tokenize(segment)
        if not tokens:
            continue
        if contains_rm_rf(tokens):
            reasons.append("rm with recursive and force flags")
        if contains_force_push(tokens):
            reasons.append("git push with force flag")
        for nested in nested_shell_commands(tokens):
            reasons.extend(detect_dangers(nested))

    sql_text = sql_text_for_command(command)
    if sql_context(command, sql_text):
        if re.search(r"(?is)\bdrop\s+table\b", sql_text):
            reasons.append("DROP TABLE statement")
        if re.search(r"(?is)\btruncate(?:\s+table)?\b", sql_text):
            reasons.append("TRUNCATE statement")
        if delete_without_where(sql_text):
            reasons.append("DELETE FROM without WHERE clause")

    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def project_path_from(payload: dict) -> str:
    for key in ("cwd", "project_path", "projectPath", "workspacePath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_blocked(command: str, project_path: str, reasons: list[str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "attempted_command": command,
        "project_path": project_path,
        "reasons": reasons,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(command: str, project_path: str, reasons: list[str]) -> None:
    log_blocked(command, project_path, reasons)
    reason_text = "; ".join(reasons)
    response = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command before execution: "
                f"{reason_text}. The command was logged to {LOG_PATH}."
            ),
        }
    }
    print(json.dumps(response))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") not in (None, HOOK_EVENT_NAME):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reasons = detect_dangers(command)
    if reasons:
        deny(command, project_path_from(payload), reasons)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
