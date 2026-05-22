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


LOG_PATH = Path(
    os.environ.get("CLAUDE_HOOK_LOG_PATH", Path.home() / ".claude" / "hooks" / "blocked.log")
)


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name")
    if isinstance(tool_name, str):
        return tool_name.lower() == "bash"
    return bool(extract_command(payload))


def has_recursive_force_rm(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        recursive = False
        force = False
        for candidate in tokens[index + 1 :]:
            if candidate == "--":
                break
            if candidate == "--recursive":
                recursive = True
                continue
            if candidate == "--force":
                force = True
                continue
            if candidate.startswith("-") and "r" in candidate.lower() and "f" in candidate.lower():
                return True
            if candidate.startswith("-") and "r" in candidate.lower():
                recursive = True
            if candidate.startswith("-") and "f" in candidate.lower():
                force = True
            if recursive and force:
                return True
    return False


def has_force_push(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        if any(arg in {"--force", "--force-with-lease", "-f"} for arg in push_args):
            return True
    return False


def has_delete_without_where(statement: str) -> bool:
    if not re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE):
        return False
    return not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE)


def sql_reason(command: str) -> str | None:
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "SQL DROP TABLE is blocked"
    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return "SQL TRUNCATE is blocked"

    statements = [part.strip() for part in command.split(";") if part.strip()]
    if any(has_delete_without_where(statement) for statement in statements):
        return "SQL DELETE FROM without WHERE is blocked"

    return None


def block_reason(command: str) -> str | None:
    if has_recursive_force_rm(command):
        return "rm with recursive and force flags is blocked"
    if has_force_push(command):
        return "git push with force is blocked"
    return sql_reason(command)


def log_blocked_attempt(payload: dict[str, Any], command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cwd = payload.get("cwd") or payload.get("project_dir") or os.getcwd()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"{timestamp}\tcwd={cwd}\treason={reason}\tcommand={command}\n"
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def allow() -> None:
    print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked dangerous Bash command: {reason}",
                }
            }
        )
    )


def main() -> int:
    payload = load_payload()
    if not is_bash_tool(payload):
        allow()
        return 0

    command = extract_command(payload)
    reason = block_reason(command)
    if not reason:
        allow()
        return 0

    try:
        log_blocked_attempt(payload, command, reason)
    except OSError as error:
        reason = f"{reason}; failed to write blocked log: {error}"
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
