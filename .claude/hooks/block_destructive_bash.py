#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any


BLOCK_EXIT_CODE = 2
SAFE_EXIT_CODE = 0
LOG_PATH = pathlib.Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockResult:
    blocked: bool
    reason: str = ""


def read_payload() -> dict[str, Any]:
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        return {}
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    for key in ("command", "cmd", "input"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str):
        return True
    return tool_name.lower() == "bash"


def delete_from_without_where(command: str) -> bool:
    statements = [part.strip() for part in command.split(";") if part.strip()]
    for statement in statements:
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, flags=re.IGNORECASE
        ):
            return True
    return False


def evaluate_command(command: str) -> BlockResult:
    checks: list[tuple[str, str]] = [
        (r"\brm\s+(?:-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r)\b", "rm -rf can recursively delete files"),
        (r"\bdrop\s+table\b", "DROP TABLE can destroy database schema"),
        (r"\bgit\s+push\b[^\n;]*\s(?:--force|-f)\b", "git push --force can overwrite remote history"),
        (r"\btruncate\b", "TRUNCATE can erase table data"),
    ]

    for pattern, reason in checks:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return BlockResult(blocked=True, reason=reason)

    if delete_from_without_where(command):
        return BlockResult(blocked=True, reason="DELETE FROM without WHERE can erase all table rows")

    return BlockResult(blocked=False)


def append_log(payload: dict[str, Any], command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "command": command,
        "project_path": project_path(payload),
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = read_payload()
    if not is_bash_tool(payload):
        return SAFE_EXIT_CODE

    command = extract_command(payload)
    if not command:
        return SAFE_EXIT_CODE

    result = evaluate_command(command)
    if not result.blocked:
        return SAFE_EXIT_CODE

    append_log(payload, command, result.reason)
    print(
        "Blocked destructive Bash command before execution: "
        f"{result.reason}. Use a narrower, reviewed command instead.",
        file=sys.stderr,
    )
    return BLOCK_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
