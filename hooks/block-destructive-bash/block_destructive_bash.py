#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"\brm\s+(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)", re.IGNORECASE),
        "Recursive force deletion is blocked.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE statements are blocked.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^;&|\n]*--force(?:\b|=|-)", re.IGNORECASE),
        "Force-pushing is blocked.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE statements are blocked.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b|;).)*(?:;|$)", re.IGNORECASE | re.DOTALL),
        "DELETE FROM statements must include a WHERE clause.",
    ),
)


def load_event(stdin: str) -> dict[str, Any]:
    try:
        event = json.loads(stdin or "{}")
    except json.JSONDecodeError:
        return {}

    return event if isinstance(event, dict) else {}


def command_from_event(event: dict[str, Any]) -> str:
    if event.get("tool_name") != "Bash":
        return ""

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def find_block_reason(command: str) -> tuple[str, str] | None:
    for rule_name, pattern, message in RULES:
        if pattern.search(command):
            return rule_name, message
    return None


def log_block(event: dict[str, Any], command: str, rule_name: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": event.get("cwd") or os.getcwd(),
        "rule": rule_name,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(command: str, rule_name: str, message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"{message} Matched policy: {rule_name}. "
                        "Revise the command to use a safe, explicit alternative."
                    ),
                }
            }
        )
    )


def main() -> int:
    event = load_event(sys.stdin.read())
    command = command_from_event(event)
    if not command:
        return 0

    block_reason = find_block_reason(command)
    if block_reason is None:
        return 0

    rule_name, message = block_reason
    log_block(event, command, rule_name)
    deny(command, rule_name, message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
