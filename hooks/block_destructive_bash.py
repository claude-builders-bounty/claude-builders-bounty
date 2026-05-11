#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code hook JSON from stdin. For Bash tool calls, it denies
commands that match a small set of high-risk destructive patterns and appends a
log entry to ~/.claude/hooks/blocked.log.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-([A-Za-z]*f[A-Za-z]*r))[A-Za-z]*\b", re.I),
        "rm -rf recursively deletes files without confirmation",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.I),
        "DROP TABLE can permanently remove database tables",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.I),
        "TRUNCATE can permanently remove table data",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;|&]*\s(?:--force|-f|--force-with-lease)\b", re.I),
        "force pushing can rewrite shared Git history",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b)[^;\n])*($|;)", re.I | re.S),
        "DELETE FROM without a WHERE clause can remove every row",
    ),
)


def _load_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        # Bad hook input should not brick normal Claude usage.
        print(f"block_destructive_bash: invalid hook JSON: {exc}", file=sys.stderr)
        sys.exit(0)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            return tool_input
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "projectDir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def find_block_reason(command: str) -> str | None:
    for label, pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return f"Blocked pattern '{label}': {reason}."
    return None


def log_blocked(command: str, project_path: str, reason: str) -> Path:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


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


def main() -> int:
    payload = _load_payload()
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = _project_path(payload)
    log_path = log_blocked(command, project_path, reason)
    deny(f"{reason} Attempted command was logged to {log_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
