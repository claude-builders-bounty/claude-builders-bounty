#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks high-risk Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


RULES = (
    ("rm -rf", re.compile(r"(^|[;&|]\s*)(sudo\s+)?rm\s+.*(?:-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r|-r\s+-f|-f\s+-r)\b", re.I | re.S)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.I)),
    ("git push --force", re.compile(r"(^|[;&|]\s*)git\s+push\b[^\n;]*\s--force(?:\s|=|$)", re.I)),
)


def command_from_payload(payload: Dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def project_path_from_payload(payload: Dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "project_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    workspace = payload.get("workspace")
    if isinstance(workspace, dict):
        value = workspace.get("project_path") or workspace.get("cwd")
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def unsafe_delete_without_where(command: str) -> bool:
    statements = re.split(r";|\n", command)
    for statement in statements:
        normalized = " ".join(statement.split()).lower()
        if re.search(r"\bdelete\s+from\b", normalized) and " where " not in f" {normalized} ":
            return True
    return False


def blocked_reason(command: str) -> Optional[str]:
    for name, pattern in RULES:
        if pattern.search(command):
            return name
    if unsafe_delete_without_where(command):
        return "DELETE FROM without WHERE"
    return None


def log_blocked_attempt(command: str, reason: str, project_path: str) -> Path:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "reason": reason,
        "project_path": project_path,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"block_destructive_commands: invalid JSON input: {error}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    command = command_from_payload(payload)
    reason = blocked_reason(command)
    if reason is None:
        return 0

    log_path = log_blocked_attempt(command, reason, project_path_from_payload(payload))
    print(
        f"Blocked destructive Bash command ({reason}). Review {log_path} for details.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
