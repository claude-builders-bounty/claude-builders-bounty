#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


BLOCKED_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "recursive forced deletion",
        re.compile(r"(?i)(^|[;&|]\s*)rm\s+(?:-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)(?:\s|$)"),
        "`rm -rf` can delete large parts of the project or system.",
    ),
    (
        "drop table",
        re.compile(r"(?i)\bdrop\s+table\b"),
        "`DROP TABLE` permanently removes database tables.",
    ),
    (
        "force push",
        re.compile(r"(?i)\bgit\s+push\b[^\n;&|]*\s--force(?:\s|$|=)|\bgit\s+push\b[^\n;&|]*\s-f(?:\s|$)"),
        "`git push --force` can overwrite remote history.",
    ),
    (
        "truncate",
        re.compile(r"(?i)\btruncate\b"),
        "`TRUNCATE` removes table data without row-level safeguards.",
    ),
    (
        "delete without where",
        re.compile(r"(?is)\bdelete\s+from\s+[\w.\"`-]+(?:(?!\bwhere\b).)*(?:;|$)"),
        "`DELETE FROM` without a `WHERE` clause can wipe an entire table.",
    ),
]


def read_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_input": {"command": raw}}
    return payload if isinstance(payload, dict) else {}


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    for key in ("command", "cmd", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def project_path(payload: dict) -> str:
    cwd = payload.get("cwd") or payload.get("project_path")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.getcwd()


def blocked_reason(command: str) -> tuple[str, str] | None:
    for name, pattern, explanation in BLOCKED_PATTERNS:
        if pattern.search(command):
            return name, explanation
    return None


def write_log(command: str, project: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps({"timestamp": timestamp, "project_path": project, "reason": reason, "command": command}) + "\n")


def main() -> int:
    payload = read_payload()
    command = extract_command(payload)
    if not command:
        return 0

    result = blocked_reason(command)
    if result is None:
        return 0

    reason, explanation = result
    project = project_path(payload)
    write_log(command, project, reason)
    print(f"Blocked destructive bash command: {reason}. {explanation}", file=sys.stderr)
    print("Use a safer, scoped command or ask the user to explicitly approve the destructive operation.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
