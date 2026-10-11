#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive force removal", re.compile(r"\brm\s+(?:-[^-\s]*[rf][^-\s]*\s+|--(?:recursive|force)(?:\s+|=))", re.I)),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force(?:-with-lease)?|-f)\b", re.I)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[A-Za-z_\"`[]", re.I)),
    ("DELETE without WHERE", re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b).)*$", re.I | re.S)),
)


def command_from_event(event: dict) -> str:
    tool_name = event.get("tool_name") or event.get("tool", {}).get("name")
    tool_input = event.get("tool_input") or event.get("input") or {}
    if isinstance(tool_input, str):
        return tool_input if tool_name in (None, "Bash", "bash") else ""
    if tool_name not in (None, "Bash", "bash"):
        return ""
    return str(tool_input.get("command", ""))


def match_rule(command: str) -> str | None:
    for label, pattern in RULES:
        if pattern.search(command):
            return label
    return None


def append_log(reason: str, command: str, project_path: str) -> None:
    log_path = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": timestamp, "reason": reason, "command": command, "project_path": project_path}, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Claude Code safety hook could not read its JSON input: {exc}", file=sys.stderr)
        return 0

    command = command_from_event(event)
    reason = match_rule(command)
    if reason is None:
        return 0

    project_path = str(event.get("cwd") or os.getcwd())
    try:
        append_log(reason, command, project_path)
    except OSError as exc:
        print(f"Claude Code safety hook could not write blocked.log: {exc}", file=sys.stderr)

    print(f"BLOCKED: {reason}. Review the command and run it manually only after confirming the destructive operation is intended.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
