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
from typing import Iterable


BLOCK_DECISION = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "",
    }
}

SQL_EXECUTORS = {
    "clickhouse-client",
    "duckdb",
    "mariadb",
    "mysql",
    "pgcli",
    "psql",
    "sqlite",
    "sqlite3",
    "sqlcmd",
}

TEXT_ONLY_COMMANDS = {
    "awk",
    "cat",
    "echo",
    "grep",
    "less",
    "more",
    "printf",
    "rg",
    "sed",
}


def split_shell_tokens(command: str) -> list[str]:
    """Best-effort shell tokenization; fall back to whitespace splitting."""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def token_basename(token: str) -> str:
    return Path(token).name.lower()


def subcommands(tokens: Iterable[str]) -> list[list[str]]:
    chunks: list[list[str]] = [[]]
    for token in tokens:
        if token in {";", "&&", "||", "|"}:
            if chunks[-1]:
                chunks.append([])
            continue
        chunks[-1].append(token)
    return [chunk for chunk in chunks if chunk]


def has_recursive_force_flags(args: list[str]) -> bool:
    seen_recursive = False
    seen_force = False

    for arg in args:
        if arg == "--":
            break
        if arg in {"-r", "-R", "--recursive"}:
            seen_recursive = True
            continue
        if arg in {"-f", "--force"}:
            seen_force = True
            continue
        if arg.startswith("-") and not arg.startswith("--"):
            flags = arg[1:]
            seen_recursive = seen_recursive or "r" in flags.lower()
            seen_force = seen_force or "f" in flags.lower()

    return seen_recursive and seen_force


def blocks_rm_rf(tokens: list[str]) -> bool:
    for chunk in subcommands(tokens):
        for index, token in enumerate(chunk):
            if token_basename(token) == "rm" and has_recursive_force_flags(chunk[index + 1 :]):
                return True
    return False


def blocks_git_force_push(tokens: list[str]) -> bool:
    for chunk in subcommands(tokens):
        for index, token in enumerate(chunk):
            if token_basename(token) != "git":
                continue

            remainder = chunk[index + 1 :]
            if "push" not in remainder:
                continue

            push_index = remainder.index("push")
            push_args = remainder[push_index + 1 :]
            for arg in push_args:
                if arg == "--":
                    break
                if arg in {"-f", "--force"} or arg.startswith("--force-with-lease"):
                    return True

    return False


def strip_sql_comments(command: str) -> str:
    command = re.sub(r"--.*?(?=\n|$)", " ", command)
    return re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)


def sql_is_text_only(tokens: list[str]) -> bool:
    first_command = token_basename(tokens[0]) if tokens else ""
    executors = {token_basename(token) for token in tokens}
    return first_command in TEXT_ONLY_COMMANDS and not (executors & SQL_EXECUTORS)


def delete_from_without_where(sql: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement = sql[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    tokens = split_shell_tokens(command)

    if blocks_rm_rf(tokens):
        return "Blocked destructive recursive removal: rm -rf."

    if blocks_git_force_push(tokens):
        return "Blocked force push: git push --force can rewrite shared history."

    sql = strip_sql_comments(command)
    if not sql_is_text_only(tokens):
        if re.search(r"\bdrop\s+table\b", sql, flags=re.IGNORECASE):
            return "Blocked destructive SQL: DROP TABLE."
        if re.search(r"\btruncate\b", sql, flags=re.IGNORECASE):
            return "Blocked destructive SQL: TRUNCATE."
        if delete_from_without_where(sql):
            return "Blocked destructive SQL: DELETE FROM without a WHERE clause."

    return None


def hooks_dir() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "hooks"


def log_blocked_attempt(command: str, cwd: str, reason: str) -> None:
    log_dir = hooks_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    safe_command = " ".join(command.splitlines())
    line = f"{timestamp}\tcwd={cwd}\treason={reason}\tcommand={safe_command}\n"
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(line)


def deny(reason: str) -> int:
    output = json.loads(json.dumps(BLOCK_DECISION))
    output["hookSpecificOutput"]["permissionDecisionReason"] = (
        f"{reason} Choose a safer, targeted command and ask the user before retrying."
    )
    print(json.dumps(output))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command")
    if not isinstance(command, str):
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    log_blocked_attempt(command, str(payload.get("cwd", "")), reason)
    return deny(reason)


if __name__ == "__main__":
    sys.exit(main())
