#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks dangerous Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DENY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recursive force delete with rm -rf", re.compile(r"(?ix)(^|[;&|]\s*)rm\s+(?=[^\n;&|]*-[^\s;&|]*r)(?=[^\n;&|]*-[^\s;&|]*f)[^\n;&|]*")),
    ("SQL DROP TABLE statement", re.compile(r"(?ix)\bdrop\s+table\b")),
    ("forced git push", re.compile(r"(?ix)(^|[;&|]\s*)git\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b")),
    ("SQL TRUNCATE statement", re.compile(r"(?ix)\btruncate\b")),
    ("SQL DELETE statement without WHERE clause", re.compile(r"(?is)\bdelete\s+from\b(?![^;]*\bwhere\b)")),
)


def load_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        deny(f"Could not parse hook input JSON: {exc}")
        raise SystemExit(0)


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def find_block_reason(command: str) -> str | None:
    for label, pattern in DENY_PATTERNS:
        if pattern.search(command):
            return label
    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = load_input()
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked(command=command, project_path=project_path, reason=reason)
    deny(f"Blocked dangerous Bash command: {reason}. The attempt was logged to ~/.claude/hooks/blocked.log.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
