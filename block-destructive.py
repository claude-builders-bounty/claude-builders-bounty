#!/usr/bin/env python3
"""Block a small, explicit set of destructive Bash commands for Claude Code."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive rm", re.compile(r"(?<![\w-])rm\s+(?:-[^-\s]*r[^-\s]*|--recursive)(?:\s|$)", re.I)),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    ("forced git push", re.compile(r"\bgit\s+push\b[^\n;|&]*\s(?:--force(?:-with-lease)?|-f)(?:\s|$)", re.I)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.I)),
    ("DELETE without WHERE", re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b).)*(?:;|$)", re.I | re.S)),
)


def extract_command(event: object) -> tuple[str, str]:
    if not isinstance(event, dict) or event.get("tool_name") != "Bash":
        return "", ""
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return "", str(event.get("cwd") or "")
    command = tool_input.get("command")
    if not isinstance(command, str):
        return "", str(event.get("cwd") or "")
    return command, str(event.get("cwd") or "")


def find_rule(command: str) -> str | None:
    for label, pattern in RULES:
        if pattern.search(command):
            return label
    return None


def log_block(cwd: str, command: str, reason: str) -> None:
    log_path = Path(os.environ.get("CLAUDE_HOOK_LOG", "~/.claude/hooks/blocked.log")).expanduser()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.touch(mode=0o600)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempted_command": command,
            "project_path": cwd,
            "reason": reason,
        }
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        try:
            log_path.chmod(0o600)
        except OSError:
            pass
    except OSError:
        print(f"Warning: could not write block log at {log_path}", file=sys.stderr)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    command, cwd = extract_command(event)
    reason = find_rule(command) if command else None
    if reason is None:
        return 0

    log_block(cwd, command, reason)
    print(
        "BLOCKED by destructive-command guard: "
        f"{reason}. Review the command and run it manually only if you intend it.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
