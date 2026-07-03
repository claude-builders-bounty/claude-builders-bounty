#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

Expected input: JSON on stdin from Claude Code hook runtime.
The hook inspects common command fields and exits non-zero when a dangerous
command is detected.
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

DANGEROUS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("recursive force delete", re.compile(r"\brm\s+(?:-[^\s]*[rf][^\s]*|-[^\s]*r[^\s]*\s+-[^\s]*f[^\s]*|-[^\s]*f[^\s]*\s+-[^\s]*r[^\s]*)\b")),
    ("DROP TABLE statement", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:-with-lease)?\b", re.IGNORECASE)),
    ("TRUNCATE statement", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\s+[^;\n]+(?:;|$)", re.IGNORECASE)),
]


def extract_command(payload: Any) -> str:
    """Extract a shell command from known Claude Code hook payload shapes."""
    if not isinstance(payload, dict):
        return ""

    direct_keys = ("command", "cmd", "input", "tool_input")
    for key in direct_keys:
        value = payload.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            nested = extract_command(value)
            if nested:
                return nested

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            if isinstance(tool_input.get(key), str):
                return tool_input[key]

    return ""


def delete_from_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\s+[^;\n]+", command, flags=re.IGNORECASE):
        statement = match.group(0)
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def detect_reason(command: str) -> str | None:
    if delete_from_without_where(command):
        return "DELETE FROM without WHERE"
    for reason, pattern in DANGEROUS_PATTERNS:
        if reason == "DELETE FROM without WHERE":
            continue
        if pattern.search(command):
            return reason
    return None


def log_block(command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    project_path = os.getcwd()
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "timestamp": timestamp,
            "reason": reason,
            "command": command,
            "project_path": project_path,
        }, ensure_ascii=False) + "\n")


def main() -> int:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {"command": raw}

    command = extract_command(payload)
    reason = detect_reason(command)
    if not reason:
        return 0

    log_block(command, reason)
    print(
        f"Blocked dangerous bash command: {reason}. "
        f"This attempt was logged to {LOG_PATH}. "
        "If you really need this operation, ask the user for explicit approval and use a safer command.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
