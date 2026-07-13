#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive shell commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "bash", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    for key in ("command", "cmd", "bash", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "projectPath"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value

    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    normalized = normalize_command(command)
    lowered = normalized.lower()

    if re.search(r"(^|[;&|]\s*)(sudo\s+)?rm\s+[^;&|]*-(?:[a-z]*r[a-z]*f|[a-z]*f[a-z]*r)", lowered):
        return "rm -rf recursively deletes files and is blocked by the safety hook"

    if re.search(r"\bgit\s+push\b[^;&|]*(--force|-f)\b", lowered):
        return "force-pushing can overwrite shared history and is blocked by the safety hook"

    if re.search(r"\bdrop\s+table\b", lowered):
        return "DROP TABLE is destructive and is blocked by the safety hook"

    if re.search(r"\btruncate\b", lowered):
        return "TRUNCATE is destructive and is blocked by the safety hook"

    if re.search(r"\bdelete\s+from\b", lowered) and not re.search(r"\bwhere\b", lowered):
        return "DELETE FROM without a WHERE clause can delete every row and is blocked by the safety hook"

    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "command": command,
                    "project_path": project_path,
                    "reason": reason,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Safety hook could not parse JSON input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("Safety hook expected a JSON object from Claude Code.", file=sys.stderr)
        return 1

    command = extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    log_block(command, project_path, reason)
    print(
        "Blocked destructive bash command before execution: "
        f"{reason}. Command: {normalize_command(command)}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
