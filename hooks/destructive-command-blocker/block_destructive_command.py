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


BLOCKED_LOG = Path(
    os.environ.get(
        "CLAUDE_BLOCKED_LOG_PATH",
        Path.home() / ".claude" / "hooks" / "blocked.log",
    )
)


def normalize_sql(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip()


def delete_from_without_where(command: str) -> bool:
    sql = normalize_sql(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement = sql[match.start() :]
        statement = re.split(r";|&&|\|\||\n", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def rm_force_recursive(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return bool(re.search(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f", command))

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        has_force = False
        has_recursive = False
        for option in tokens[index + 1 :]:
            if option == "--":
                break
            if not option.startswith("-"):
                break
            if option in {"--force"}:
                has_force = True
                continue
            if option in {"--recursive", "--dir"}:
                has_recursive = True
                continue
            if option.startswith("-") and not option.startswith("--"):
                option_letters = option.lstrip("-")
                has_force = has_force or "f" in option_letters
                has_recursive = has_recursive or "r" in option_letters or "R" in option_letters

        if has_force and has_recursive:
            return True
    return False


def git_push_force(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return bool(re.search(r"\bgit\s+push\b.*\B--force\b", command, flags=re.IGNORECASE))

    for index, token in enumerate(tokens):
        if token != "git":
            continue
        if index + 1 >= len(tokens) or tokens[index + 1] != "push":
            continue
        push_args = tokens[index + 2 :]
        if any(arg == "-f" or arg == "--force" or arg.startswith("--force-with-lease") for arg in push_args):
            return True
    return False


def blocking_reason(command: str) -> str | None:
    if rm_force_recursive(command):
        return "recursive force delete (rm -rf)"
    if git_push_force(command):
        return "force push (git push --force)"
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "DROP TABLE statement"
    if re.search(r"\btruncate\s+(?:table\s+)?[A-Za-z_]", command, flags=re.IGNORECASE):
        return "TRUNCATE statement"
    if delete_from_without_where(command):
        return "DELETE FROM without a WHERE clause"
    return None


def read_hook_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def log_blocked(command: str, cwd: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": cwd,
        "reason": reason,
        "command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command: {reason}. "
                f"The attempt was logged to {BLOCKED_LOG}."
            ),
        }
    }
    print(json.dumps(response))


def main() -> int:
    payload = read_hook_input()
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = blocking_reason(command)
    if reason is None:
        return 0

    log_blocked(command=command, cwd=str(payload.get("cwd") or ""), reason=reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
