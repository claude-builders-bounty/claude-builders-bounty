#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

The hook accepts Claude Code hook JSON on stdin. It is intentionally tolerant of
slightly different payload shapes so it can be used across Claude Code versions
and wrappers.
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

BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("rm -rf / rm -fr", re.compile(r"(^|[;&|]\s*)rm\s+[^\n;&|]*(?:-[a-zA-Z]*r[a-zA-Z]*f|- [^\n;&|]*r[^\n;&|]*f|- [^\n;&|]*f[^\n;&|]*r)", re.I)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*(--force|-f)\b", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.I)),
]

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.I)
WHERE_RE = re.compile(r"\bwhere\b", re.I)


def extract_command(payload: dict[str, Any]) -> str:
    """Extract a bash command from common Claude hook payload shapes."""
    candidates: list[Any] = [
        payload.get("command"),
        payload.get("input", {}).get("command") if isinstance(payload.get("input"), dict) else None,
        payload.get("tool_input", {}).get("command") if isinstance(payload.get("tool_input"), dict) else None,
        payload.get("parameters", {}).get("command") if isinstance(payload.get("parameters"), dict) else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate

    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    for name, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return name

    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return "DELETE FROM without WHERE"

    return None


def log_block(reason: str, command: str, path: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{path}\t{reason}\t{safe_command}\n")


def deny(reason: str, command: str, path: str) -> int:
    log_block(reason, command, path)
    message = (
        f"Blocked destructive bash command: {reason}. "
        f"The attempted command was logged to {LOG_PATH}. "
        "Revise the command to be narrower, reversible, or explicitly confirmed by the user."
    )
    print(json.dumps({"decision": "block", "reason": message}))
    return 2


def allow() -> int:
    print(json.dumps({"decision": "allow"}))
    return 0


def main() -> int:
    try:
        raw = sys.stdin.read() or "{}"
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Invalid hook input should not break safe commands.
        return allow()

    if not isinstance(payload, dict):
        return allow()

    command = extract_command(payload)
    if not command:
        return allow()

    reason = blocked_reason(command)
    if reason:
        return deny(reason, command, project_path(payload))

    return allow()


if __name__ == "__main__":
    raise SystemExit(main())
