#!/usr/bin/env python3
"""Block destructive Bash commands in Claude Code PreToolUse hooks."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_COMMANDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "recursive forced deletion",
        re.compile(
            r"(?i)(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)"
        ),
    ),
    (
        "SQL DROP TABLE statement",
        re.compile(r"(?is)\bdrop\s+table\b"),
    ),
    (
        "force push",
        re.compile(r"(?i)(?:^|[;&|]\s*)git\s+push\b[^;&|]*(?:--force|-f\b|--force-with-lease)"),
    ),
    (
        "SQL TRUNCATE statement",
        re.compile(r"(?is)\btruncate(?:\s+table)?\b"),
    ),
    (
        "DELETE statement without WHERE clause",
        re.compile(r"(?is)\bdelete\s+from\b(?![^;&|]*\bwhere\b)"),
    ),
)


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid hook JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("hook JSON must be an object")

    return payload


def extract_command(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    if not isinstance(command, str):
        return ""

    return command


def find_block_reason(command: str) -> str | None:
    command = command.strip()
    if not command:
        return None

    for reason, pattern in BLOCKED_COMMANDS:
        if pattern.search(command):
            return reason

    return None


def project_dir(payload: dict[str, Any]) -> Path:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd)

    env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project_dir:
        return Path(env_project_dir)

    return Path.cwd()


def hooks_dir() -> Path:
    env_hooks_dir = os.environ.get("CLAUDE_HOOKS_DIR")
    if env_hooks_dir:
        return Path(env_hooks_dir)

    return Path.home() / ".claude" / "hooks"


def write_block_log(payload: dict[str, Any], command: str, reason: str) -> None:
    log_dir = hooks_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    cwd = str(project_dir(payload))

    entry = {
        "timestamp": timestamp,
        "project_path": cwd,
        "reason": reason,
        "command": command,
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = load_payload()
    except ValueError as exc:
        print(f"Hook input error: {exc}", file=sys.stderr)
        return 0

    command = extract_command(payload)
    reason = find_block_reason(command)

    if reason is None:
        return 0

    try:
        write_block_log(payload, command, reason)
    except OSError as exc:
        print(
            f"Blocked destructive command, but could not write ~/.claude/hooks/blocked.log: {exc}",
            file=sys.stderr,
        )
        return 2

    print(
        "Blocked destructive Bash command: "
        f"{reason}. This command was not executed and was recorded in ~/.claude/hooks/blocked.log.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
