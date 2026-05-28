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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def main() -> int:
    payload = read_payload()
    tool_name = str(payload.get("tool_name", ""))

    if tool_name != "Bash":
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked_attempt(command, project_path, reason)
    print(json.dumps(deny_response(reason), separators=(",", ":")))
    return 0


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    return ""


def block_reason(command: str) -> str | None:
    checks = (
        blocks_rm_rf,
        blocks_git_force_push,
        blocks_drop_table,
        blocks_truncate,
        blocks_delete_without_where,
    )

    for check in checks:
        reason = check(command)
        if reason:
            return reason

    return None


def blocks_rm_rf(command: str) -> str | None:
    for argv in split_commands(command):
        argv = executable_argv(argv)
        if not argv or Path(argv[0]).name != "rm":
            continue

        recursive = False
        force = False
        for arg in argv[1:]:
            if arg == "--":
                break
            if arg.startswith("--"):
                recursive = recursive or arg == "--recursive"
                force = force or arg == "--force"
                continue
            if arg.startswith("-"):
                recursive = recursive or "r" in arg or "R" in arg
                force = force or "f" in arg

        if recursive and force:
            return "Blocked destructive remove command: rm with recursive and force flags."

    return None


def blocks_git_force_push(command: str) -> str | None:
    for argv in split_commands(command):
        argv = executable_argv(argv)
        if len(argv) < 3 or Path(argv[0]).name != "git" or argv[1] != "push":
            continue

        if any(arg == "-f" or arg.startswith("--force") for arg in argv[2:]):
            return "Blocked force push: git push with --force or -f can rewrite remote history."

    return None


def blocks_drop_table(command: str) -> str | None:
    for statement in sql_statements(command):
        if re.search(r"\bdrop\s+table\b", statement, flags=re.IGNORECASE):
            return "Blocked SQL schema deletion: DROP TABLE can permanently remove data."
    return None


def blocks_truncate(command: str) -> str | None:
    for statement in sql_statements(command):
        if re.search(r"\btruncate\b", statement, flags=re.IGNORECASE):
            return "Blocked SQL truncation: TRUNCATE can remove all rows from a table."
    return None


def blocks_delete_without_where(command: str) -> str | None:
    for statement in sql_statements(command):
        match = re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE)
        if not match:
            continue

        tail = statement[match.end() :]
        if not re.search(r"\bwhere\b", tail, flags=re.IGNORECASE):
            return "Blocked broad SQL delete: DELETE FROM must include a WHERE clause."

    return None


def split_commands(command: str) -> list[list[str]]:
    return shell_segments(command)


def shell_segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    segments: list[list[str]] = [[]]

    try:
        tokens = list(lexer)
    except ValueError:
        return []

    for token in tokens:
        if token in {";", "&&", "||"}:
            segments.append([])
        else:
            segments[-1].append(token)

    return [segment for segment in segments if segment]


def executable_argv(argv: list[str]) -> list[str]:
    while argv and is_assignment(argv[0]):
        argv = argv[1:]

    if argv and Path(argv[0]).name == "sudo":
        argv = strip_sudo(argv[1:])

    if argv and Path(argv[0]).name == "env":
        argv = strip_env(argv[1:])

    return argv


def strip_sudo(argv: list[str]) -> list[str]:
    while argv and argv[0].startswith("-"):
        argv = argv[1:]
    while argv and is_assignment(argv[0]):
        argv = argv[1:]
    return argv


def strip_env(argv: list[str]) -> list[str]:
    while argv and (argv[0].startswith("-") or is_assignment(argv[0])):
        argv = argv[1:]
    return argv


def is_assignment(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", value))


def sql_statements(command: str) -> list[str]:
    statements: list[str] = []
    for argv in split_commands(command):
        argv = executable_argv(argv)
        if not argv:
            continue

        client = Path(argv[0]).name
        if client in {"psql", "mysql", "mariadb"}:
            statements.extend(sql_from_flag(argv, "-c"))
            statements.extend(sql_from_flag(argv, "-e"))
        elif client == "sqlite3" and len(argv) >= 3:
            statements.extend(argv[2:])

    return statements


def sql_from_flag(argv: list[str], flag: str) -> list[str]:
    statements: list[str] = []
    for index, arg in enumerate(argv):
        if arg == flag and index + 1 < len(argv):
            statements.append(argv[index + 1])
        elif arg.startswith(flag) and len(arg) > len(flag):
            statements.append(arg[len(flag) :])
    return statements


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": redact_command(command),
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


def redact_command(command: str) -> str:
    redacted = re.sub(
        r"(?i)\b(password|passwd|token|api[_-]?key|secret)=([^\s;]+)",
        r"\1=<redacted>",
        command,
    )
    redacted = re.sub(
        r"(?i)(--(?:password|token|api-key|secret)(?:=|\s+))([^\s;]+)",
        r"\1<redacted>",
        redacted,
    )
    redacted = re.sub(
        r"(?i)(authorization:\s*(?:bearer\s+)?)([^\s'\";]+)",
        r"\1<redacted>",
        redacted,
    )
    return redacted


def deny_response(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


if __name__ == "__main__":
    raise SystemExit(main())
