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
    os.environ.get(
        "CLAUDE_HOOKS_BLOCKED_LOG",
        str(Path.home() / ".claude" / "hooks" / "blocked.log"),
    )
)


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_sql_comments(command: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", without_block_comments)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    command = payload.get("command")
    if isinstance(command, str):
        return command

    return ""


def _extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "working_directory"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd")
        if isinstance(value, str) and value:
            return value

    return os.getcwd()


def _has_forced_recursive_rm(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        flags = set()
        for candidate in tokens[index + 1 :]:
            if candidate == "--":
                break
            if not candidate.startswith("-"):
                continue
            if candidate in ("--recursive", "--force"):
                flags.add(candidate)
                continue
            if candidate.startswith("--"):
                continue
            flags.update(candidate[1:])

        if ("r" in flags or "R" in flags or "--recursive" in flags) and (
            "f" in flags or "--force" in flags
        ):
            return True

    return False


def _has_forced_git_push(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        return any(arg == "-f" or arg.startswith("--force") for arg in push_args)

    return False


def _delete_without_where(sql: str) -> bool:
    normalized = _collapse_whitespace(_strip_sql_comments(sql)).upper()
    if not re.search(r"\bDELETE\s+FROM\b", normalized):
        return False

    statements = [part.strip() for part in normalized.split(";") if part.strip()]
    for statement in statements:
        if re.search(r"\bDELETE\s+FROM\b", statement) and not re.search(
            r"\bWHERE\b", statement
        ):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    normalized_sql = _collapse_whitespace(_strip_sql_comments(command)).upper()

    if _has_forced_recursive_rm(command):
        return "recursive forced deletion (`rm -rf`) is blocked"
    if _has_forced_git_push(command):
        return "force pushing (`git push --force`) is blocked"
    if re.search(r"\bDROP\s+TABLE\b", normalized_sql):
        return "dropping tables (`DROP TABLE`) is blocked"
    if re.search(r"\bTRUNCATE\b", normalized_sql):
        return "truncating data (`TRUNCATE`) is blocked"
    if _delete_without_where(command):
        return "broad deletes (`DELETE FROM` without `WHERE`) are blocked"

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={safe_command}\n"
        )


def build_response(blocked: bool, message: str) -> dict[str, Any]:
    if blocked:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }
    return {}


def main() -> int:
    raw_payload = sys.stdin.read().strip()
    try:
        payload = json.loads(raw_payload) if raw_payload else {}
    except json.JSONDecodeError:
        payload = {"command": raw_payload}

    command = _extract_command(payload)
    project_path = _extract_project_path(payload)
    reason = blocked_reason(command)

    if reason:
        log_blocked_attempt(command, project_path, reason)
        response = build_response(
            True,
            f"Blocked destructive Bash command: {reason}. Review the command and ask the user for explicit approval before proceeding.",
        )
        print(json.dumps(response))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
