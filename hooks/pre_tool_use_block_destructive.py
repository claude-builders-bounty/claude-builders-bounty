#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("recursive forced delete", re.compile(r"(?i)(^|[;&|]\s*)rm\s+-[a-z]*r[a-z]*f[a-z]*\b")),
    ("force push", re.compile(r"(?i)\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b")),
    ("drop table", re.compile(r"(?i)\bdrop\s+table\b")),
    ("truncate table", re.compile(r"(?i)\btruncate\s+(?:table\s+)?[a-zA-Z0-9_.\"`]+")),
    ("delete without where", re.compile(r"(?is)\bdelete\s+from\b(?![^;\n]*\bwhere\b)")),
]


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def command_from_payload(payload: dict) -> str:
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}

    if tool_name.lower() != "bash":
        return ""

    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")

    return ""


def find_block_reason(command: str) -> str | None:
    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason
    return None


def log_block(payload: dict, command: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked-destructive-commands.log"
    project = payload.get("cwd") or payload.get("workspace") or os.getcwd()
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file.write_text(
        "",
        encoding="utf-8",
    ) if not log_file.exists() else None
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\treason={reason}\tproject={project}\tcommand={command!r}\n")


def main() -> int:
    payload = load_payload()
    command = command_from_payload(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    log_block(payload, command, reason)
    print(
        f"Blocked destructive Bash command ({reason}). Review the command and use a safer, explicit alternative.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
