#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)
SQL_EXECUTORS = {
    "mysql",
    "mariadb",
    "psql",
    "sqlite3",
    "sqlcmd",
    "duckdb",
    "clickhouse-client",
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Blocked: invalid Claude Code hook JSON: {exc}", file=sys.stderr)
        return 2

    if payload.get("tool_name") != "Bash":
        return 0

    command = str((payload.get("tool_input") or {}).get("command") or "")
    project_path = str(
        payload.get("cwd")
        or payload.get("project_path")
        or payload.get("workspace")
        or os.getcwd()
    )

    reason = find_block_reason(command)
    if reason is None:
        return 0

    log_blocked(command, project_path, reason)
    print(
        "Blocked destructive Bash command before execution: "
        f"{reason}. Ask the user for explicit confirmation or use a safer command.",
        file=sys.stderr,
    )
    return 2


def find_block_reason(command: str) -> str | None:
    for segment in split_shell_segments(command):
        words = shell_words(segment)
        if not words:
            continue

        offset = command_offset(words)
        if offset >= len(words):
            continue

        executable = command_name(words[offset])
        args = words[offset + 1 :]

        if executable == "rm" and has_recursive_force(args):
            return "rm with both recursive and force flags is not allowed"

        if executable == "git" and is_force_push(args):
            return "git push with force is not allowed"

        if executable in {"bash", "sh", "zsh"}:
            nested_script = shell_script_from_invocation(args)
            if nested_script:
                nested_reason = find_block_reason(nested_script)
                if nested_reason:
                    return nested_reason

        if executable in {"echo", "printf", "grep", "rg", "ack", "sed", "cat"}:
            continue

        if is_sql_execution(executable, args):
            sql_text = sql_text_from_invocation(args)
            sql_reason = find_sql_reason(sql_text)
            if sql_reason:
                return sql_reason

        if looks_like_raw_sql(segment):
            sql_reason = find_sql_reason(segment)
            if sql_reason:
                return sql_reason

    return None


def split_shell_segments(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0

    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            index += 1
            continue

        if quote:
            current.append(char)
            if char == quote:
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            current.append(char)
            index += 1
            continue

        two_chars = command[index : index + 2]
        if char in {";", "\n", "|", "&"} or two_chars in {"&&", "||"}:
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
            index += 2 if two_chars in {"&&", "||"} else 1
            continue

        current.append(char)
        index += 1

    segment = "".join(current).strip()
    if segment:
        segments.append(segment)
    return segments


def shell_words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return segment.split()


def command_offset(words: list[str]) -> int:
    index = 0
    while index < len(words) and is_env_assignment(words[index]):
        index += 1
    if index < len(words) and command_name(words[index]) == "sudo":
        index += 1
        while index < len(words) and words[index].startswith("-"):
            index += 1
    if index < len(words) and command_name(words[index]) in {"env", "command"}:
        index += 1
        while index < len(words) and (
            is_env_assignment(words[index]) or words[index].startswith("-")
        ):
            index += 1
    return index


def is_env_assignment(word: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", word))


def command_name(word: str) -> str:
    return Path(word).name.lower()


def has_recursive_force(args: list[str]) -> bool:
    recursive = False
    force = False
    for arg in args:
        if arg == "--":
            break
        if not arg.startswith("-") or arg == "-":
            continue
        if arg == "--recursive":
            recursive = True
        elif arg == "--force":
            force = True
        elif arg.startswith("--"):
            continue
        else:
            flags = arg.lstrip("-").lower()
            recursive = recursive or "r" in flags or "R".lower() in flags
            force = force or "f" in flags
        if recursive and force:
            return True
    return False


def is_force_push(args: list[str]) -> bool:
    try:
        push_index = next(index for index, arg in enumerate(args) if arg == "push")
    except StopIteration:
        return False
    push_args = args[push_index + 1 :]
    return any(arg in {"--force", "-f", "--force-with-lease"} for arg in push_args)


def shell_script_from_invocation(args: list[str]) -> str | None:
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-c" and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith("-") and "c" in arg[1:] and index + 1 < len(args):
            return args[index + 1]
        index += 1
    return None


def is_sql_execution(executable: str, args: list[str]) -> bool:
    if executable in SQL_EXECUTORS:
        return True
    if executable in {"python", "python3", "node", "bash", "sh"}:
        return False
    return any(arg.lower().endswith((".sql", ".psql")) for arg in args)


def sql_text_from_invocation(args: list[str]) -> str:
    inline_parts: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {"-e", "-c", "--command", "--execute"} and index + 1 < len(args):
            inline_parts.append(args[index + 1])
            index += 2
            continue
        if arg.startswith(("-e=", "-c=", "--command=", "--execute=")):
            inline_parts.append(arg.split("=", 1)[1])
        index += 1
    return "\n".join(inline_parts) if inline_parts else " ".join(args)


def find_sql_reason(text: str) -> str | None:
    if DROP_TABLE_RE.search(text):
        return "DROP TABLE statements are not allowed"
    if TRUNCATE_RE.search(text):
        return "TRUNCATE statements are not allowed"

    for statement in split_sql_statements(text):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "DELETE FROM without WHERE is not allowed"
    return None


def looks_like_raw_sql(text: str) -> bool:
    return bool(
        re.match(
            r"^\s*(drop\s+table|truncate(?:\s+table)?|delete\s+from)\b",
            text,
            re.IGNORECASE,
        )
    )


def split_sql_statements(text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char in {";", "\n"}:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue
        current.append(char)

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements


def log_blocked(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
