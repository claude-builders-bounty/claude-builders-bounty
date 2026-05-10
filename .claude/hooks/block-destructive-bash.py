#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin and denies Bash commands that match
high-risk patterns such as rm -rf, force pushes, or broad SQL destructive
statements. Blocked attempts are appended to ~/.claude/hooks/blocked.log.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("recursive forced deletion (rm -rf)", re.compile(r"(?:^|[;&|`$()\s])rm\s+[^\n;&|]*-[^\n;&|]*r[^\n;&|]*f|(?:^|[;&|`$()\s])rm\s+[^\n;&|]*-[^\n;&|]*f[^\n;&|]*r", re.IGNORECASE)),
    ("SQL DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("forced git push", re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=)|\bgit\s+push\b[^\n;&|]*\s-f(?:\b|\s)", re.IGNORECASE)),
    ("SQL TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
    ("SQL DELETE without WHERE", re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b)[^;\n])*($|;|\n)", re.IGNORECASE)),
]


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "project_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project:
        return env_project
    return os.getcwd()


def _first_block_reason(command: str) -> str | None:
    for reason, pattern in PATTERNS:
        if pattern.search(command):
            return reason
    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: " + reason +
                ". Review the command, make it narrower/reversible, or run it manually if intentional."
            ),
        }
    }))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed hook input: fail open so normal non-hook workflows are not broken.
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = _first_block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
