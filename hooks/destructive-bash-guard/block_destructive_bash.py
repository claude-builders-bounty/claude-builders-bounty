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


def load_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def get_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    if isinstance(command, str):
        return command

    return ""


def get_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "workspace_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "workdir", "working_directory"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value

    return os.getcwd()


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name")
    if isinstance(tool_name, str):
        return tool_name.lower() in {"bash", "shell", "shell_command"}

    # Tests and older hook payloads may only include tool_input.command.
    return bool(get_command(payload))


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # If the shell fragment is malformed, fall back to regex checks.
        return []


def blocks_rm_rf(command: str) -> bool:
    tokens = shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        for arg in tokens[index + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue
            flags = arg.lstrip("-")
            if "r" in flags and "f" in flags:
                return True

    return bool(re.search(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f|(^|[;&|]\s*)rm\s+-[A-Za-z]*f[A-Za-z]*r", command))


def blocks_git_force_push(command: str) -> bool:
    tokens = shell_tokens(command)
    for index in range(0, max(len(tokens) - 2, 0)):
        if tokens[index : index + 2] != ["git", "push"]:
            continue
        push_args = tokens[index + 2 :]
        if any(arg == "--force" or arg == "-f" or arg.startswith("--force-with-lease") for arg in push_args):
            return True

    return bool(re.search(r"(^|[;&|]\s*)git\s+push\b[^\n;&|]*(--force\b|-f\b|--force-with-lease\b)", command))


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", sql)


def blocks_sql(command: str) -> str | None:
    tokens = shell_tokens(command)
    if tokens and tokens[0] in {"grep", "rg", "ag", "ack", "echo", "printf"}:
        return None

    normalized = strip_sql_comments(command)

    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "DROP TABLE can destroy schema and data."

    if re.search(r"\btruncate\b", normalized, flags=re.IGNORECASE):
        return "TRUNCATE can remove all rows from a table."

    delete_matches = re.finditer(
        r"\bdelete\s+from\b(?P<body>.*?)(?:;|$)",
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in delete_matches:
        statement = match.group("body")
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return "DELETE FROM without a WHERE clause can remove every row."

    return None


def find_block_reason(command: str) -> str | None:
    if blocks_rm_rf(command):
        return "rm -rf style commands can recursively and forcibly delete files."

    sql_reason = blocks_sql(command)
    if sql_reason:
        return sql_reason

    if blocks_git_force_push(command):
        return "git push --force can overwrite remote history."

    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "project_path": project_path,
            "attempted_command": command,
            "reason": reason,
        },
        ensure_ascii=False,
    )
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")


def allow() -> None:
    print(json.dumps({"continue": True}))


def deny(reason: str) -> None:
    message = f"Blocked destructive Bash command: {reason}"
    print(
        json.dumps(
            {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                },
            }
        )
    )


def main() -> int:
    payload = load_payload()
    if not is_bash_tool(payload):
        allow()
        return 0

    command = get_command(payload)
    if not command:
        allow()
        return 0

    reason = find_block_reason(command)
    if not reason:
        allow()
        return 0

    log_blocked(command=command, project_path=get_project_path(payload), reason=reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
