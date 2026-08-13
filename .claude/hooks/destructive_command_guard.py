#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands.

Reads the Claude Code hook JSON payload from stdin. If the hook is invoked for
Bash and the command matches a destructive pattern, logs the attempt and exits
non-zero so Claude Code blocks the tool call.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "rm -rf",
        re.compile(
            r"(?:^|[;&|()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "rm --recursive --force",
        re.compile(
            r"(?:^|[;&|()\s])rm\b"
            r"(?=[^\n;&|]*\s--recursive\b)"
            r"(?=[^\n;&|]*\s--force\b)",
            re.IGNORECASE,
        ),
    ),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b)[^;\n])*($|[;\n])", re.IGNORECASE),
    ),
]


def _load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        # If Claude Code ever passes raw text, treat it as a command defensively.
        return {"tool_name": "Bash", "tool_input": {"command": raw}}


def _extract_command(payload: dict[str, Any]) -> str | None:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        return None

    for key in ("command", "cmd", "script"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value

    # Some hook wrappers send the command at top level.
    value = payload.get("command")
    return value if isinstance(value, str) else None


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "transcript_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            if key == "transcript_path":
                return str(Path(value).parent)
            return value
    return os.getcwd()


def _match_rule(command: str) -> str | None:
    for name, pattern in BLOCK_RULES:
        if pattern.search(command):
            return name
    return None


def _log_block(rule: str, command: str, project_path: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\trule={rule}\tproject={project_path}\tcommand={safe_command}\n")


def main() -> int:
    payload = _load_payload()
    command = _extract_command(payload)
    if not command:
        return 0

    rule = _match_rule(command)
    if not rule:
        return 0

    project_path = _project_path(payload)
    _log_block(rule, command, project_path)
    print(
        f"Blocked destructive Bash command ({rule}). "
        f"Review the command manually before running it. Logged to {LOG_PATH}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
