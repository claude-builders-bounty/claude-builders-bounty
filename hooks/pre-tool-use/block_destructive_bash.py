#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash/SQL commands."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DESTRUCTIVE_RULES = [
    (
        re.compile(r"\brm\s+-[^\n]*r[^\n]*f|\brm\s+-[^\n]*f[^\n]*r|\brm\s+--recursive\s+--force|\brm\s+--force\s+--recursive", re.IGNORECASE),
        "rm -rf (recursive force deletion)",
    ),
    (
        re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
        "DROP TABLE / DATABASE / SCHEMA",
    ),
    (
        re.compile(r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?|\s-f\b)", re.IGNORECASE),
        "git push --force / -f",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_.\"`]+", re.IGNORECASE),
        "TRUNCATE table",
    ),
    (
        re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.\"`]+(?![^;]*\bWHERE\b)", re.IGNORECASE),
        "DELETE FROM without a WHERE clause",
    ),
]


def log_blocked(command: str, reason: str, cwd: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{ts}] project={cwd} | reason={reason} | command={command}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def evaluate_command(command: str) -> str | None:
    for pattern, label in DESTRUCTIVE_RULES:
        if pattern.search(command):
            return label
    return None


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name and tool_name != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    cwd = str(payload.get("cwd") or os.getcwd())
    if not command:
        return 0

    matched_reason = evaluate_command(command)
    if matched_reason:
        log_blocked(command, matched_reason, cwd)
        msg = (
            f"Blocked destructive command ({matched_reason}). "
            f"Logged to {LOG_PATH}. Verify scope or use a safer command."
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": msg,
                    }
                }
            )
        )
        print(msg, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
