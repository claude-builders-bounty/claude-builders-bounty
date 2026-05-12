#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "recursive force removal",
        re.compile(r"(^|[;&|]\s*)rm\s+-(?:[A-Za-z]*r[A-Za-z]*f|[A-Za-z]*f[A-Za-z]*r)\b"),
        "Refusing to run rm -rf style deletion.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "Refusing to run a DROP TABLE statement.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "Refusing to run a TRUNCATE statement.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b"),
        "Refusing to run a force push.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b|;).)*($|;)", re.IGNORECASE | re.DOTALL),
        "Refusing to run DELETE FROM without a WHERE clause.",
    ),
)


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def project_path(payload: dict) -> str:
    for key in ("cwd", "project_path", "workspace", "root"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def find_block_reason(command: str) -> tuple[str, str] | None:
    for rule_name, pattern, message in BLOCK_RULES:
        if pattern.search(command):
            return rule_name, message

    return None


def log_block(command: str, rule_name: str, project: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    normalized_command = " ".join(command.split())
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{project}\t{rule_name}\t{normalized_command}\n")


def main() -> int:
    payload = load_payload()

    if payload.get("tool_name") != "Bash":
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    blocked = find_block_reason(command)
    if not blocked:
        return 0

    rule_name, message = blocked
    project = project_path(payload)
    log_block(command, rule_name, project)

    print(
        f"{message} This command matched the '{rule_name}' safety rule. "
        f"Use a narrower, reviewed command or ask the user for explicit confirmation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
