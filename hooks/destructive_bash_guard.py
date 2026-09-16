#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
CLAUDE_EVENT = "PreToolUse"

COMMAND_BREAKS = {";", "&&", "||", "|", "\n"}
SQL_CLIENTS = {
    "mysql",
    "mariadb",
    "psql",
    "sqlite3",
    "sqlcmd",
    "duckdb",
    "clickhouse-client",
}
TEXT_ONLY_COMMANDS = {"cat", "echo", "grep", "printf", "rg", "sed"}


def main() -> int:
    payload = _read_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    project_path = _project_path(payload)
    reason = detect_destructive_command(command)

    if not reason:
        return 0

    _log_blocked_attempt(command, project_path, reason)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": CLAUDE_EVENT,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked destructive Bash command before execution: "
                        f"{reason}. Rewrite the command to use a safer, scoped operation "
                        "or ask the user for explicit manual confirmation."
                    ),
                }
            },
            separators=(",", ":"),
        )
    )
    return 0


def _read_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _project_path(payload: dict) -> str:
    for key in ("cwd", "project_dir", "project_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as log_file:
        writer = csv.writer(log_file)
        writer.writerow([timestamp, project_path, reason, command])


def detect_destructive_command(command: str) -> str | None:
    tokens = _shell_tokens(command)
    if not tokens:
        return None

    for segment in _command_segments(tokens):
        reason = _detect_rm_rf(segment) or _detect_git_force_push(segment) or _detect_sql(segment)
        if reason:
            return reason
    return None


def _shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def _command_segments(tokens: Iterable[str]) -> Iterable[list[str]]:
    segment: list[str] = []
    for token in tokens:
        if token in COMMAND_BREAKS:
            if segment:
                yield segment
                segment = []
            continue
        segment.append(token)
    if segment:
        yield segment


def _base_command(token: str) -> str:
    return Path(token).name.lower()


def _detect_rm_rf(segment: list[str]) -> str | None:
    if not segment or _base_command(segment[0]) != "rm":
        return None

    flags = "".join(token[1:] for token in segment[1:] if re.fullmatch(r"-[A-Za-z]+", token))
    long_flags = {token for token in segment[1:] if token.startswith("--")}
    has_recursive = "r" in flags or "R" in flags or "--recursive" in long_flags
    has_force = "f" in flags or "--force" in long_flags
    if has_recursive and has_force:
        return "rm was invoked with recursive and force flags"
    return None


def _detect_git_force_push(segment: list[str]) -> str | None:
    if len(segment) < 3 or _base_command(segment[0]) != "git" or segment[1].lower() != "push":
        return None

    force_flags = {"--force", "-f", "--force-with-lease", "--force-if-includes"}
    for token in segment[2:]:
        if token in force_flags or token.startswith("--force-with-lease="):
            return "git push was invoked with a force flag"
    return None


def _detect_sql(segment: list[str]) -> str | None:
    if not segment or _base_command(segment[0]) in TEXT_ONLY_COMMANDS:
        return None

    text = " ".join(segment)
    if _base_command(segment[0]) not in SQL_CLIENTS and not _looks_like_sql(text):
        return None

    for statement in _sql_statements(text):
        normalized = _normalize_sql(statement)
        if re.search(r"\bdrop\s+table\b", normalized, re.IGNORECASE):
            return "DROP TABLE statement detected"
        if re.search(r"\btruncate\b", normalized, re.IGNORECASE):
            return "TRUNCATE statement detected"
        if re.search(r"\bdelete\s+from\b", normalized, re.IGNORECASE) and not re.search(
            r"\bwhere\b", normalized, re.IGNORECASE
        ):
            return "DELETE FROM statement without a WHERE clause detected"
    return None


def _looks_like_sql(text: str) -> bool:
    return bool(
        re.search(
            r"\b(drop\s+table|truncate|delete\s+from)\b",
            text,
            re.IGNORECASE,
        )
    )


def _sql_statements(text: str) -> list[str]:
    without_comments = re.sub(r"--[^\n]*", " ", text)
    return [part.strip() for part in without_comments.split(";") if part.strip()]


def _normalize_sql(statement: str) -> str:
    return re.sub(r"\s+", " ", statement).strip()


if __name__ == "__main__":
    raise SystemExit(main())
