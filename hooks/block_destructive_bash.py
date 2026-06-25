#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path


BLOCK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "recursive force delete",
        re.compile(
            r"\brm\s+(?:(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)"
            r"|(?:--recursive\s+--force|--force\s+--recursive))\b"
        ),
    ),
    ("SQL DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b")),
    ("SQL TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    ("SQL DELETE without WHERE", re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.IGNORECASE)),
)


def load_event() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        return {"tool_name": "unknown", "tool_input": {}, "parse_error": str(exc)}


def command_from_event(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("input") or ""
        return str(command)
    return str(tool_input)


def blocked_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason
    return None


def log_block(command: str, reason: str, event: dict) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    project_path = (
        event.get("cwd")
        or event.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    entry = {
        "timestamp": _dt.datetime.now(_dt.UTC).isoformat(),
        "reason": reason,
        "command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def main() -> int:
    event = load_event()
    if event.get("tool_name") not in {"Bash", "bash", None, "unknown"}:
        return 0

    command = command_from_event(event)
    reason = blocked_reason(command)
    if not reason:
        return 0

    log_path = log_block(command, reason, event)
    print(
        "Blocked destructive Bash command: "
        f"{reason}. The attempt was logged to {log_path}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
