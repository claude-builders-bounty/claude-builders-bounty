#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


BLOCKERS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(
            r"(^|[;&|]\s*)(?:sudo\s+)?rm\s+"
            r"(?=[^\n;|&]*(?:-[^\n;|&]*r|--recursive\b))"
            r"(?=[^\n;|&]*(?:-[^\n;|&]*f|--force\b))[^\n;|&]*"
        ),
        "recursive force delete can remove large parts of the filesystem",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.I),
        "DROP TABLE destroys schema and data",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.I),
        "TRUNCATE deletes table data without row-level review",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;|&]*(--force|-f\b|--force-with-lease)"),
        "force-pushing can overwrite remote history",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b).)*($|;)", re.I | re.S),
        "DELETE FROM without WHERE can wipe an entire table",
    ),
]


def emit_decision(permission: str, reason: str | None = None) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": permission,
        }
    }
    if reason:
        output["hookSpecificOutput"]["permissionDecisionReason"] = reason
    print(json.dumps(output))


def extract_command(payload: dict[str, object]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or payload.get("arguments") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        return str(command)
    return ""


def project_path(payload: dict[str, object]) -> str:
    for key in ("cwd", "project_path", "workspace"):
        value = payload.get(key)
        if value:
            return str(value)
    return os.getcwd()


def find_block(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in BLOCKERS:
        if pattern.search(command):
            return name, reason
    return None


def log_block(command: str, path: str, pattern: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": path,
        "pattern": pattern,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":")) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        emit_decision("deny", f"Invalid hook payload: {exc}")
        return 0

    command = extract_command(payload)
    if not command:
        emit_decision("allow")
        return 0

    blocked = find_block(command)
    if blocked is None:
        emit_decision("allow")
        return 0

    pattern, reason = blocked
    path = project_path(payload)
    log_block(command, path, pattern)
    emit_decision(
        "deny",
        f"Blocked destructive Bash command ({pattern}): {reason}. "
        f"The attempt was logged to {LOG_PATH}.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
