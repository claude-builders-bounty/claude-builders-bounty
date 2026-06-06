#!/usr/bin/env python3
"""Claude Code pre-tool-use hook for blocking destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def extract_command(payload: dict[str, Any]) -> str:
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}

    if tool_name.lower() != "bash":
        return ""

    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        return str(command)

    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if value:
            return str(value)

    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "projectPath"):
            value = tool_input.get(key)
            if value:
                return str(value)

    return os.getcwd()


def strip_strings_and_comments(command: str) -> str:
    cleaned: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0

    while index < len(command):
        char = command[index]

        if escaped:
            escaped = False
            index += 1
            continue

        if char == "\\":
            escaped = True
            index += 1
            continue

        if quote:
            if char == quote:
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            index += 1
            continue

        if char == "#":
            while index < len(command) and command[index] != "\n":
                index += 1
            continue

        cleaned.append(char)
        index += 1

    return "".join(cleaned)


def delete_without_where(command: str) -> bool:
    checked = strip_strings_and_comments(command)
    statements = re.split(r"[;\n]", checked)
    for statement in statements:
        if re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
                return True
    return False


def blocked_reason(command: str) -> str | None:
    checks = [
        (r"\brm\s+[^\n;]*-(?:[^\s-]*r[^\s-]*f|[^\s-]*f[^\s-]*r)\b", "rm -rf can delete files recursively"),
        (r"\bDROP\s+TABLE\b", "DROP TABLE can destroy database tables"),
        (r"\bgit\s+push\b[^\n;]*(?:--force(?:-with-lease)?|\s-f(?:\s|$))", "forced git pushes can rewrite shared history"),
        (r"\bTRUNCATE\b", "TRUNCATE can erase table contents"),
    ]

    checked = strip_strings_and_comments(command)
    for pattern, reason in checks:
        if re.search(pattern, checked, re.IGNORECASE):
            return reason

    if delete_without_where(command):
        return "DELETE FROM without WHERE can erase every matching row"

    return None


def log_block(command: str, path: str, reason: str) -> None:
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "command": command,
            "project_path": path,
            "reason": reason,
        },
        ensure_ascii=False,
    )
    with BLOCK_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Destructive command hook could not read Claude hook payload: {error}", file=sys.stderr)
        return 1

    command = extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    path = project_path(payload)
    log_block(command, path, reason)
    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {reason}.\n"
        f"Project: {path}\n"
        f"Command: {command}\n"
        f"Logged to: {BLOCK_LOG}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
