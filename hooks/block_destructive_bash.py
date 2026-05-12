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


DELETE_WITHOUT_WHERE_RE = re.compile(r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", re.IGNORECASE | re.DOTALL)


BLOCK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\brm\s+-[^\n;]*r[^\n;]*f\b|\brm\s+-[^\n;]*f[^\n;]*r\b", re.IGNORECASE), "rm -rf"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:\s|$)", re.IGNORECASE), "git push --force"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (DELETE_WITHOUT_WHERE_RE, "DELETE FROM without WHERE"),
)


def extract_command(payload: dict[str, Any]) -> str:
    """Return the Bash command from Claude Code hook JSON input."""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    return command if isinstance(command, str) else ""


def find_block_reason(command: str) -> str | None:
    """Return a human-readable block reason when command is destructive."""
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def build_decision(command: str, reason: str) -> dict[str, Any]:
    """Build a Claude Code PreToolUse deny decision."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {reason}. Command was not executed.",
        }
    }


def write_block_log(log_path: Path, command: str, project_path: str) -> None:
    """Append one blocked attempt to the hook log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} command={command} project_path={project_path}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = extract_command(payload)
    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    write_block_log(log_path, command, project_path)
    print(json.dumps(build_decision(command, reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
