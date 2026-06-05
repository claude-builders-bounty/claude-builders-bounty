#!/usr/bin/env python3
"""Block destructive Bash commands from Claude Code PreToolUse hooks."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b(?P<tail>[^;]*)", re.IGNORECASE | re.DOTALL)


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def is_rm_token(token: str) -> bool:
    return token == "rm" or token.endswith("/rm")


def has_rm_rf(command: str) -> bool:
    tokens = split_command(command)

    for index, token in enumerate(tokens):
        if not is_rm_token(token):
            continue

        recursive = False
        force = False
        for option in tokens[index + 1 :]:
            if not option.startswith("-"):
                break
            if option in {"--recursive", "--dir"}:
                recursive = True
            if option == "--force":
                force = True
            if option.startswith("-") and not option.startswith("--"):
                recursive = recursive or "r" in option or "R" in option
                force = force or "f" in option

        if recursive and force:
            return True

    return False


def has_force_push(command: str) -> bool:
    tokens = split_command(command)

    for index, token in enumerate(tokens):
        if token != "git" and not token.endswith("/git"):
            continue

        after_git = tokens[index + 1 :]
        if "push" not in after_git:
            continue

        push_index = after_git.index("push")
        push_options = after_git[push_index + 1 :]
        if any(
            option in {"--force", "--force-with-lease", "-f"}
            or option.startswith("--force-with-lease=")
            for option in push_options
        ):
            return True

    return False


def has_sql_destructive_statement(command: str) -> str | None:
    if DROP_TABLE_RE.search(command):
        return "DROP TABLE"

    if TRUNCATE_RE.search(command):
        return "TRUNCATE"

    for match in DELETE_FROM_RE.finditer(command):
        tail = match.group("tail")
        if not re.search(r"\bWHERE\b", tail, re.IGNORECASE):
            return "DELETE FROM without WHERE"

    return None


def find_block_reason(command: str) -> str | None:
    if has_rm_rf(command):
        return "rm -rf"

    sql_reason = has_sql_destructive_statement(command)
    if sql_reason:
        return sql_reason

    if has_force_push(command):
        return "git push --force"

    return None


def project_path(payload: dict[str, Any]) -> str:
    return (
        payload.get("cwd")
        or payload.get("project_path")
        or payload.get("workspace_path")
        or os.getcwd()
    )


def log_path() -> Path:
    configured = os.environ.get("CLAUDE_BLOCKER_LOG")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(payload: dict[str, Any], command: str, reason: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path(payload),
        "reason": reason,
        "command": command,
    }

    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    payload = load_payload()

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = find_block_reason(command)
    if not reason:
        return 0

    log_blocked_attempt(payload, command, reason)
    print(f"Blocked destructive Bash command: {reason}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
