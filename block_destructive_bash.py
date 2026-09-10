#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook intentionally uses only the Python standard library so it can be
installed on a fresh machine. It reads the PreToolUse JSON object from stdin
and emits a deny decision only when a destructive command is detected.
"""

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
COMMAND_BOUNDARIES = {";", "&&", "||", "|", "&", "(", ")"}
WRAPPERS = {"command", "env", "nohup", "sudo"}
SQL_CLIENTS = {
    "bq",
    "duckdb",
    "mariadb",
    "mysql",
    "pgcli",
    "psql",
    "sqlite3",
    "sqlcmd",
}
SQL_FLAG_NAMES = {"-c", "--command", "-e", "--execute"}


def _tokens(command: str) -> list[str]:
    """Tokenize a shell command while preserving command boundaries.

    Invalid or incomplete shell syntax should not make the safety hook fail
    open. Returning a whitespace-based tokenization still lets the detector
    catch the dangerous forms in that case.
    """

    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = "#"
        return list(lexer)
    except ValueError:
        return command.split()


def _segments(tokens: Sequence[str]) -> Iterable[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in COMMAND_BOUNDARIES:
            if current:
                yield current
                current = []
            continue
        current.append(token)
    if current:
        yield current


def _command_index(segment: Sequence[str]) -> int | None:
    """Return the executable index after common shell wrappers."""

    index = 0
    while index < len(segment):
        token = segment[index]
        if token in WRAPPERS:
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                # Skip wrapper options (for example, sudo -n or nohup -p).
                index += 1
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.+", token):
            index += 1
            continue
        return index
    return None


def _rm_reason(segment: Sequence[str], index: int) -> str | None:
    if os.path.basename(segment[index]) != "rm":
        return None

    flags: list[str] = []
    for token in segment[index + 1 :]:
        if token == "--":
            break
        if token.startswith("-"):
            flags.append(token.lower())

    has_recursive = any(
        flag in {"--recursive", "-r", "-R".lower()}
        or (flag.startswith("-") and not flag.startswith("--") and "r" in flag[1:])
        for flag in flags
    )
    has_force = any(
        flag in {"--force", "-f"}
        or (flag.startswith("-") and not flag.startswith("--") and "f" in flag[1:])
        for flag in flags
    )
    if has_recursive and has_force:
        return "Blocked destructive command: recursive force removal (rm -rf)."
    return None


def _git_reason(segment: Sequence[str], index: int) -> str | None:
    if os.path.basename(segment[index]) != "git":
        return None

    try:
        push_index = next(i for i in range(index + 1, len(segment)) if segment[i] == "push")
    except StopIteration:
        return None

    for token in segment[push_index + 1 :]:
        if token in {"--force", "-f"} or token.startswith("--force="):
            return "Blocked destructive command: force push (git push --force)."
    return None


def _sql_reason(sql: str) -> str | None:
    """Find destructive SQL, allowing safe DELETE statements with WHERE."""

    for statement in re.split(r";", sql):
        if re.search(r"\bDROP\s+TABLE\b", statement, re.IGNORECASE):
            return "Blocked destructive command: DROP TABLE."
        if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", statement, re.IGNORECASE):
            return "Blocked destructive command: TRUNCATE."

        delete = re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE)
        if delete and not re.search(r"\bWHERE\b", statement[delete.end() :], re.IGNORECASE):
            return "Blocked destructive command: DELETE FROM without a WHERE clause."
    return None


def _sql_in_segment(segment: Sequence[str], index: int) -> str | None:
    executable = os.path.basename(segment[index]).lower()
    if executable not in SQL_CLIENTS:
        return None

    for position, token in enumerate(segment[index + 1 :], start=index + 1):
        if token.lower() in SQL_FLAG_NAMES:
            sql = " ".join(segment[position + 1 :])
            reason = _sql_reason(sql)
            if reason:
                return reason
    return None


def detect_reason(command: str) -> str | None:
    """Return a human-readable block reason, or ``None`` for safe commands."""

    tokens = _tokens(command)
    for segment in _segments(tokens):
        index = _command_index(segment)
        if index is None:
            continue

        reason = _rm_reason(segment, index) or _git_reason(segment, index)
        if reason:
            return reason

        reason = _sql_in_segment(segment, index)
        if reason:
            return reason

        # Also catch a direct SQL command supplied as the shell segment itself.
        raw_segment = " ".join(segment[index:])
        reason = _sql_reason(raw_segment)
        if reason and os.path.basename(segment[index]).lower() in {
            "drop",
            "truncate",
            "delete",
        }:
            return reason
    return None


def _input_data() -> dict:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _log_block(data: dict, command: str, reason: str) -> bool:
    project_path = data.get("cwd") or data.get("project_path") or os.environ.get("CLAUDE_PROJECT_DIR") or ""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "project_path": os.path.abspath(str(project_path)) if project_path else "",
        "reason": reason,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def main() -> int:
    data = _input_data()
    tool_name = data.get("tool_name")
    if tool_name is not None and tool_name != "Bash":
        return 0

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = detect_reason(command)
    if reason is None:
        return 0

    logged = _log_block(data, command, reason)
    if not logged:
        reason += " Audit logging failed; command remains blocked."

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
