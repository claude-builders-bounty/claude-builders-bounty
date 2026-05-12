#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive shell commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("drop table statement", re.compile(r"\bdrop\s+table\b", re.I)),
    ("truncate statement", re.compile(r"\btruncate\b", re.I)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:-with-lease)?\b", re.I)),
)


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"command": raw}
    return payload if isinstance(payload, dict) else {}


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_command(payload: dict[str, Any]) -> str:
    candidates = (
        nested_get(payload, ("tool_input", "command")),
        nested_get(payload, ("input", "command")),
        payload.get("command"),
        os.environ.get("CLAUDE_TOOL_COMMAND"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    candidates = (
        nested_get(payload, ("tool_input", "cwd")),
        nested_get(payload, ("input", "cwd")),
        payload.get("cwd"),
        payload.get("project_path"),
        os.environ.get("PWD"),
        os.getcwd(),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return os.getcwd()


def delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        lowered = statement.lower()
        if re.search(r"\bdelete\s+from\b", lowered) and not re.search(r"\bwhere\b", lowered):
            return True
    return False


def has_recursive_force_delete(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        flags = ""
        for next_token in tokens[index + 1 :]:
            if not next_token.startswith("-") or next_token == "--":
                break
            flags += next_token.lstrip("-")
        if "r" in flags.lower() and "f" in flags.lower():
            return True
    return False


def block_reason(command: str) -> str | None:
    if has_recursive_force_delete(command):
        return "recursive force delete"
    for reason, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    if delete_without_where(command):
        return "delete statement without WHERE clause"
    return None


def log_block(command: str, project_path: str, reason: str) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "reason": reason,
        "project_path": project_path,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return log_path


def main() -> int:
    payload = read_payload()
    command = extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    log_path = log_block(command, project_path, reason)
    print(
        "Blocked command before execution: "
        f"{reason}. Review the command and use a safer, narrower operation. "
        f"Attempt logged to {log_path}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
