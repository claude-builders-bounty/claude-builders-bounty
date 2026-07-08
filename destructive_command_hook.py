#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive shell commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive force removal", re.compile(r"\brm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b")),
    ("DROP TABLE statement", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b", re.IGNORECASE)),
    ("TRUNCATE statement", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bDELETE\s+FROM\b(?![\s\S]*?\bWHERE\b)", re.IGNORECASE),
    ),
)


def read_payload() -> Any:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])

    raw = sys.stdin.read().strip()
    if not raw:
        return ""

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def extract_command(payload: Any) -> str:
    if isinstance(payload, str):
        return payload

    if not isinstance(payload, dict):
        return json.dumps(payload, sort_keys=True)

    candidates = [
        payload.get("command"),
        payload.get("input", {}).get("command") if isinstance(payload.get("input"), dict) else None,
        payload.get("tool_input", {}).get("command") if isinstance(payload.get("tool_input"), dict) else None,
        payload.get("parameters", {}).get("command") if isinstance(payload.get("parameters"), dict) else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate

    return json.dumps(payload, sort_keys=True)


def project_path(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("cwd", "project_path", "projectPath"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return os.getcwd()


def blocked_reason(command: str) -> str | None:
    for label, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return label
    return None


def append_log(command: str, reason: str, path: str) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    log_path.open("a", encoding="utf-8").write(
        f"{timestamp}\t{reason}\t{path}\t{safe_command}\n"
    )
    return log_path


def main() -> int:
    payload = read_payload()
    command = extract_command(payload)
    path = project_path(payload)
    reason = blocked_reason(command)

    if not reason:
        return 0

    log_path = append_log(command, reason, path)
    print(
        "Blocked destructive command before execution.\n"
        f"Reason: {reason}.\n"
        f"Command: {command}\n"
        f"Project: {path}\n"
        f"Logged to: {log_path}\n"
        "Revise the command to target a safer path, add a WHERE clause, or ask the user for explicit approval.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
