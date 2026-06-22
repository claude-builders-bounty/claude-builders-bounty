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


SQL_DELETE_RE = re.compile(r"\bdelete\s+from\b(?P<body>.*?)(?:;|$)", re.IGNORECASE | re.DOTALL)
SQL_DESTRUCTIVE_RE = re.compile(r"\b(drop\s+table|truncate)\b", re.IGNORECASE)


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        # An invalid shell line should not crash the hook. Fall back to a
        # whitespace split so obvious destructive patterns are still caught.
        return command.split()


def _rm_recursive_force(command: str) -> bool:
    tokens = _shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        has_recursive = False
        has_force = False
        for flag in tokens[index + 1 :]:
            if flag == "--":
                break
            if not flag.startswith("-"):
                continue
            if flag in {"--recursive", "--dir", "-r", "-R"}:
                has_recursive = True
            else:
                has_recursive = has_recursive or "r" in flag[1:] or "R" in flag[1:]
            if flag in {"--force", "-f"}:
                has_force = True
            else:
                has_force = has_force or "f" in flag[1:]
            if has_recursive and has_force:
                return True
    return False


def _git_push_force(command: str) -> bool:
    tokens = _shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        remaining = tokens[index + 1 :]
        if not remaining or remaining[0] != "push":
            continue
        for flag in remaining[1:]:
            if flag == "--":
                break
            if flag in {"--force", "--force-with-lease", "-f"}:
                return True
            if flag.startswith("-") and "f" in flag[1:]:
                return True
    return False


def _delete_without_where(command: str) -> bool:
    for match in SQL_DELETE_RE.finditer(command):
        statement_body = match.group("body")
        if not re.search(r"\bwhere\b", statement_body, re.IGNORECASE):
            return True
    return False


def destructive_reason(command: str) -> str | None:
    if _rm_recursive_force(command):
        return "rm with recursive and force flags is blocked"
    if _git_push_force(command):
        return "force-pushing with git is blocked"
    sql_match = SQL_DESTRUCTIVE_RE.search(command)
    if sql_match:
        return f"SQL destructive operation blocked: {sql_match.group(1).upper()}"
    if _delete_without_where(command):
        return "DELETE FROM without a WHERE clause is blocked"
    return None


def _log_blocked(command: str, project_path: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project = project_path.replace("\n", "\\n")
    safe_reason = reason.replace("\n", "\\n")
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{safe_project}\t{safe_reason}\t{safe_command}\n")


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = destructive_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    _log_blocked(command, project_path, reason)
    _deny(f"Blocked destructive Bash command: {reason}. Command was not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
