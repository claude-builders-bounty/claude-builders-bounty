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


LOG_PATH = Path(os.environ.get("CLAUDE_BLOCKED_LOG_PATH", Path.home() / ".claude" / "hooks" / "blocked.log"))


BLOCK_PATTERNS = [
    (
        "rm recursive-force",
        re.compile(r"(?:^|[;&|]\s*|\b(?:sudo|env)\s+)rm\s+(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)", re.IGNORECASE),
        "Recursive force removal is blocked. Use a scoped delete or ask the user to approve it explicitly.",
    ),
    (
        "git push force",
        re.compile(r"\bgit\s+push\b(?=[^;&|]*(?:--force(?:-with-lease)?\b|-f\b))", re.IGNORECASE),
        "Force-pushing is blocked. Use a normal push or ask the user to approve rewriting remote history.",
    ),
]

DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)
READ_ONLY_SCAN_RE = re.compile(r"^\s*(?:git\s+grep|grep|rg|ag|ack)\b", re.IGNORECASE)


def delete_from_without_where(command: str) -> bool:
    """Return True when any DELETE FROM statement segment lacks a WHERE clause."""

    for match in DELETE_FROM_RE.finditer(command):
        segment = command[match.end() :]
        statement = re.split(r"[;\n\r]", segment, maxsplit=1)[0]
        if not WHERE_RE.search(statement):
            return True
    return False


def command_segment_at(command: str, index: int) -> str:
    start = max(command.rfind(separator, 0, index) for separator in (";", "&", "|", "\n", "\r"))
    end_candidates = [pos for separator in (";", "&", "|", "\n", "\r") if (pos := command.find(separator, index)) != -1]
    end = min(end_candidates) if end_candidates else len(command)
    return command[start + 1 : end]


def is_read_only_scan_match(command: str, index: int) -> bool:
    return bool(READ_ONLY_SCAN_RE.match(command_segment_at(command, index)))


def destructive_sql_reason(command: str) -> str | None:
    for match in DROP_TABLE_RE.finditer(command):
        if not is_read_only_scan_match(command, match.start()):
            return "DROP TABLE: DROP TABLE is blocked. Use a migration review flow or ask the user for explicit approval."

    for match in TRUNCATE_RE.finditer(command):
        if not is_read_only_scan_match(command, match.start()):
            return "TRUNCATE: TRUNCATE is blocked because it can delete large amounts of data."

    return None


def blocked_reason(command: str) -> str | None:
    """Return a human-readable block reason for a command, or None if safe."""

    for label, pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return f"{label}: {reason}"

    sql_reason = destructive_sql_reason(command)
    if sql_reason is not None:
        return sql_reason

    if delete_from_without_where(command):
        return "DELETE FROM without WHERE: Unqualified DELETE statements are blocked. Add a WHERE clause or ask for explicit approval."

    return None


def read_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(f"Could not parse Claude Code hook input as JSON: {exc}", file=sys.stderr)
        return {}


def log_blocked_attempt(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    safe_command = command.replace("\n", "\\n").replace("\r", "\\r")
    safe_cwd = cwd.replace("\n", "\\n").replace("\r", "\\r")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{safe_cwd}\t{reason}\t{safe_command}\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked destructive Bash command. {reason}",
                }
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    payload = read_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = blocked_reason(command)
    if reason is None:
        return 0

    cwd = str(payload.get("cwd") or "")
    log_blocked_attempt(command, cwd, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
