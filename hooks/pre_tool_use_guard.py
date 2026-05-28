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

    if re.search(r"(?<!\S)rm\s+(?:-[^\s;]*r[^\s;]*f[^\s;]*|-[^\s;]*f[^\s;]*r[^\s;]*)", command):
        return "Blocked destructive remove command: rm with recursive and force flags."

    return None


def blocks_git_force_push(command: str) -> str | None:
    for argv in split_commands(command):
        if len(argv) < 3 or Path(argv[0]).name != "git" or argv[1] != "push":
            continue

        if any(arg == "-f" or arg.startswith("--force") for arg in argv[2:]):
            return "Blocked force push: git push with --force or -f can rewrite remote history."

    if re.search(r"(?<!\S)git\s+push\b[^;\n]*(?:--force(?:-with-lease|-if-includes)?|-f)(?:\s|$)", command):
        return "Blocked force push: git push with --force or -f can rewrite remote history."

    return None


def blocks_drop_table(command: str) -> str | None:
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "Blocked SQL schema deletion: DROP TABLE can permanently remove data."
    return None


def blocks_truncate(command: str) -> str | None:
    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
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
    parts = re.split(r"[;\n]|&&|\|\|", command)
    argv_list: list[list[str]] = []

    for part in parts:
        try:
            argv = shlex.split(part, posix=True)
        except ValueError:
            argv = []
        if argv:
            argv_list.append(argv)

    return argv_list


def sql_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n|&&|\|\|", command) if part.strip()]


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


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
