#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


DENY_EVENT = "PreToolUse"


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _split_shell_segments(command: str) -> list[str]:
    return [
        segment.strip()
        for segment in re.split(r"(?:&&|\|\||;|\n)", command)
        if segment.strip()
    ]


def _skip_wrappers(tokens: list[str]) -> list[str]:
    while tokens and tokens[0] in {"sudo", "command", "exec", "nohup"}:
        tokens = tokens[1:]
        while tokens and tokens[0].startswith("-") and tokens[0] != "--":
            tokens = tokens[1:]
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
    return tokens


def _shlex_tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def _rm_force_recursive_reason(command: str) -> str | None:
    for segment in _split_shell_segments(command):
        tokens = _skip_wrappers(_shlex_tokens(segment))
        if not tokens or tokens[0] != "rm":
            continue

        short_flags: set[str] = set()
        long_flags: set[str] = set()
        for token in tokens[1:]:
            if token == "--":
                break
            if token.startswith("--"):
                long_flags.add(token)
            elif token.startswith("-"):
                short_flags.update(token[1:])

        has_recursive = "r" in short_flags or "R" in short_flags or "--recursive" in long_flags
        has_force = "f" in short_flags or "--force" in long_flags
        if has_recursive and has_force:
            return "Blocked destructive recursive force removal (`rm -rf` / equivalent)."
    return None


def _git_force_push_reason(command: str) -> str | None:
    for segment in _split_shell_segments(command):
        tokens = _skip_wrappers(_shlex_tokens(segment))
        if len(tokens) < 3 or tokens[0] != "git" or tokens[1] != "push":
            continue
        force_flags = {"--force", "--force-with-lease", "-f"}
        if any(token in force_flags or token.startswith("--force-with-lease=") for token in tokens[2:]):
            return "Blocked force-pushing with `git push --force` / equivalent."
    return None


def _strip_sql_comments(command: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", without_block_comments)


def _sql_reason(command: str) -> str | None:
    sql = _strip_sql_comments(command)
    if re.search(r"\bDROP\s+TABLE\b", sql, flags=re.IGNORECASE):
        return "Blocked destructive SQL `DROP TABLE` statement."
    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", sql, flags=re.IGNORECASE):
        return "Blocked destructive SQL `TRUNCATE` statement."

    for statement in re.split(r";|\n", sql):
        normalized = _compact(statement)
        delete_match = re.search(r"\bDELETE\s+FROM\b", normalized, flags=re.IGNORECASE)
        if delete_match and not re.search(r"\bWHERE\b", normalized[delete_match.end() :], flags=re.IGNORECASE):
            return "Blocked SQL `DELETE FROM` without a `WHERE` clause."
    return None


def find_block_reason(command: str) -> str | None:
    """Return a human-readable block reason, or None when the command is safe."""
    return (
        _rm_force_recursive_reason(command)
        or _git_force_push_reason(command)
        or _sql_reason(command)
    )


def _project_path(payload: dict[str, Any]) -> str:
    return (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or payload.get("cwd")
        or payload.get("workspace")
        or os.getcwd()
    )


def _log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "project_path": _project_path(payload),
        "attempted_command": command,
        "reason": reason,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": DENY_EVENT,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            separators=(",", ":"),
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    _log_block(payload, command, reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
