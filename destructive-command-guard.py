#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads the JSON payload Claude Code passes on stdin. For Bash tool
calls, it scans the requested command for destructive patterns, logs blocked
attempts to ~/.claude/hooks/blocked.log, and returns Claude Code's structured
PreToolUse denial response.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "rm -rf / rm -fr recursive forced delete",
        re.compile(
            r"(?:^|[;&|()\s])rm\s+(?:(?:-[\w]*r[\w]*f[\w]*|-[\w]*f[\w]*r[\w]*)|(?:--recursive\s+--force|--force\s+--recursive))(?:\s|$)",
            re.IGNORECASE,
        ),
    ),
    ("DROP TABLE statement", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    (
        "git push --force / -f",
        re.compile(
            r"\bgit\s+push\b(?=[^\n;|&]*(?:\s--force(?:\b|=)|\s-f(?:\s|$)))[^\n;|&]*",
            re.IGNORECASE,
        ),
    ),
    ("TRUNCATE statement", re.compile(r"\btruncate\b", re.IGNORECASE)),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.IGNORECASE),
    ),
)


def load_payload() -> dict[str, Any]:
    """Read a hook payload from stdin, failing open for malformed input."""

    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"destructive-command-guard: invalid JSON payload: {exc}", file=sys.stderr)
        return {}
    return payload if isinstance(payload, dict) else {}


def tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or "")


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input") or payload.get("input") or {}
    return value if isinstance(value, dict) else {}


def command_from(payload: dict[str, Any]) -> str:
    return str(tool_input(payload).get("command") or "")


def project_path_from(payload: dict[str, Any]) -> str:
    data = tool_input(payload)
    return str(
        data.get("cwd")
        or data.get("workdir")
        or payload.get("cwd")
        or payload.get("project_path")
        or payload.get("transcript_path")
        or os.getcwd()
    )


def dangerous_reason(command: str) -> str | None:
    for label, pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return label
    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny_response(reason: str) -> dict[str, Any]:
    message = (
        "Blocked destructive Bash command. "
        f"Reason: {reason}. The attempt was logged to {LOG_PATH}. "
        "Rewrite the command as a safer, scoped operation before trying again."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }


def main() -> int:
    payload = load_payload()
    if tool_name(payload).lower() != "bash":
        return 0

    command = command_from(payload)
    reason = dangerous_reason(command)
    if reason is None:
        return 0

    log_blocked(command, project_path_from(payload), reason)
    print(json.dumps(deny_response(reason), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
