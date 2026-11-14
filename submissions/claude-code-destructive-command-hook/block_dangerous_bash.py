#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude Code PreToolUse hook: block destructive Bash commands.

Reads the hook payload as JSON on stdin. If the Bash command matches a
destructive pattern, logs it and exits 2 with a clear message (Claude Code
treats exit 2 from a PreToolUse hook as a block). Otherwise exits 0.

Works on Python 3.9+ with no third-party dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.environ.get("CLAUDE_HOOK_LOG", str(Path.home() / ".claude" / "hooks" / "blocked.log")))

# Each pattern is (name, regex). Matching is case-insensitive where needed.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # rm with recursive + force flags in any order/combination
    ("rm -rf", re.compile(r"(?:^|[;&|]\s*)\s*rm\b(?=[^\n;&|]*\s-(?=[a-zA-Z]*r)(?=[a-zA-Z]*f))[^\n;&|]*", re.I)),
    # DROP TABLE (including IF EXISTS)
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    # git push --force / -f
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force\b|\s-f\b)", re.I)),
    # TRUNCATE
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.I)),
    # DELETE FROM without WHERE (statement by statement)
    ("DELETE without WHERE", re.compile(r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", re.I)),
]


def blocked_command(command: str) -> str | None:
    for name, pattern in PATTERNS:
        if pattern.search(command):
            return name
    return None


def log_block(pattern: str, command: str, cwd: str, tool_input: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pattern": pattern,
            "command": command,
            "cwd": cwd,
        }
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # Never crash the hook because logging failed.
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Malformed input: do not block normal work.
        return 0

    if payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0
    cwd = tool_input.get("cwd") or payload.get("cwd") or os.getcwd()

    pattern = blocked_command(command)
    if not pattern:
        return 0

    log_block(pattern, command, str(cwd), tool_input)
    print(
        f"Blocked by claude-hook: this command matches a destructive pattern ({pattern}).\n"
        f"Command: {command}\n"
        "If this is intentional, ask the user to run it manually or temporarily disable the hook.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
