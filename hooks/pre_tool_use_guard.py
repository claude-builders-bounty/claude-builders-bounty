#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("rm -rf", re.compile(r"(^|[;&|()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\b")),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f|--force-with-lease)\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("DELETE FROM without WHERE", re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.IGNORECASE)),
]


def project_path(payload: dict) -> str:
    return (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.getcwd()
    )


def get_command(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or ""
    return command if isinstance(command, str) else ""


def find_block_reason(command: str) -> str | None:
    for name, pattern in BLOCK_RULES:
        if pattern.search(command):
            return name
    return None


def log_blocked_attempt(command: str, reason: str, path: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{path}\t{reason}\t{safe_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"PreToolUse guard could not parse JSON input: {exc}", file=sys.stderr)
        return 0

    command = get_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    path = project_path(payload)
    log_blocked_attempt(command, reason, path)
    print(
        f"Blocked dangerous Bash command ({reason}). "
        "Use a safer command or request explicit human approval.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
