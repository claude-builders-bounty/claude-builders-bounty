#!/usr/bin/env python3
"""Claude Code pre-tool-use hook for blocking destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "recursive force delete",
        re.compile(r"(?i)(^|[;&|()])\s*(?:sudo\s+)?rm\s+(?=[^\n;&|]*-[A-Za-z]*r)(?=[^\n;&|]*-[A-Za-z]*f)[^\n;&|]*"),
    ),
    ("DROP TABLE statement", re.compile(r"(?is)\bdrop\s+table\b")),
    ("force push", re.compile(r"(?i)\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b")),
    ("TRUNCATE statement", re.compile(r"(?is)\btruncate\b")),
    ("DELETE FROM without WHERE", re.compile(r"(?is)\bdelete\s+from\b(?:(?!\bwhere\b|;).)*(?:;|$)")),
)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    for key in ("command", "cmd", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def _is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name") or payload.get("tool") or payload.get("name")
    if isinstance(tool_name, str):
        return tool_name.lower() in {"bash", "shell", "exec_command"}

    tool_input = payload.get("tool_input")
    return isinstance(tool_input, dict) and any(k in tool_input for k in ("command", "cmd", "script"))


def _project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd") or payload.get("project_path")
    if isinstance(cwd, str) and cwd:
        return cwd

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        working_dir = tool_input.get("working_dir") or tool_input.get("workdir") or tool_input.get("cwd")
        if isinstance(working_dir, str) and working_dir:
            return working_dir

    return os.getcwd()


def _blocked_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason
    return None


def _log_blocked(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "reason": reason,
        "command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Allowed: hook input was not JSON.", file=sys.stderr)
        return 0

    if not isinstance(payload, dict) or not _is_bash_tool(payload):
        return 0

    command = _extract_command(payload)
    reason = _blocked_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_blocked(command, project_path, reason)
    print(
        f"Blocked destructive bash command: {reason}. "
        "Review the command and run it manually only if you are certain it is intended.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
