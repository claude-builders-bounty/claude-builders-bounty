#!/usr/bin/env python3
"""Fail-closed PreToolUse hook for destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_RULES = (
    ("rm -rf", re.compile(r"\brm\s+(?:-[^\n]*f[^\n]*|--force[^\n]*)\s+", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)),
)
DELETE_WITHOUT_WHERE = re.compile(
    r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.IGNORECASE
)


def decision(reason: str) -> None:
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


def log_block(command: str, project_dir: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    # Keep one line per event and cap input size so a command cannot flood the log.
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")[:4096]
    safe_project = project_dir.replace("\r", "\\r").replace("\n", "\\n")[:1024]
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(
            f"{timestamp}\treason={reason}\tproject={safe_project}\tcommand={safe_command}\n"
        )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        # Invalid hook input must not silently authorize a tool call.
        decision("Blocked: hook input was not valid JSON")
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "")
    if not isinstance(command, str):
        decision("Blocked: Bash command was not a string")
        return 0

    reason = None
    for label, pattern in BLOCK_RULES:
        if pattern.search(command):
            reason = f"Destructive command blocked: {label}"
            break
    if reason is None and DELETE_WITHOUT_WHERE.search(command):
        reason = "Destructive command blocked: DELETE FROM without WHERE"

    if reason is not None:
        log_block(command, str(payload.get("cwd") or os.getcwd()), reason)
        decision(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
