#!/usr/bin/env python3
"""Claude Code PreToolUse hook for blocking destructive Bash commands.

Reads Claude Code hook JSON from stdin. If the event is a Bash tool call and the
command matches a destructive pattern, the hook logs the attempt and returns a
PreToolUse permission denial in Claude Code's JSON hook format.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_REASON_BY_PATTERN: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "recursive forced removal with rm -rf",
        re.compile(r"(?ix)(?:^|[;&|`$()\s])(?:sudo\s+)?rm\s+-[^\s;|&]*r[^\s;|&]*f|(?:^|[;&|`$()\s])(?:sudo\s+)?rm\s+-[^\s;|&]*f[^\s;|&]*r"),
    ),
    (
        "SQL DROP TABLE statement",
        re.compile(r"(?is)\bdrop\s+table\b"),
    ),
    (
        "forced git push",
        re.compile(r"(?i)\bgit\s+push\b[^\n;|&]*?(?:--force(?:-with-lease)?\b|-f\b)"),
    ),
    (
        "SQL TRUNCATE statement",
        re.compile(r"(?is)\btruncate\b"),
    ),
    (
        "SQL DELETE FROM without a WHERE clause",
        re.compile(r"(?is)\bdelete\s+from\s+[\w.\"`\[\]-]+(?:(?!\bwhere\b).)*(?:;|$)"),
    ),
)


def load_event() -> dict[str, Any]:
    """Load Claude Code hook event JSON from stdin."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Safety hook could not parse hook JSON: {exc}", file=sys.stderr)
        return {}
    if isinstance(data, dict):
        return data
    return {}


def command_from_event(event: dict[str, Any]) -> str:
    """Extract the Bash command from a Claude Code PreToolUse event."""
    if event.get("tool_name") != "Bash":
        return ""
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def project_path_from_event(event: dict[str, Any]) -> str:
    """Extract project path from event JSON or environment fallback."""
    for key in ("cwd", "project_dir", "project_path"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project:
        return env_project
    return os.getcwd()


def block_reason(command: str) -> str | None:
    """Return the reason a command should be blocked, or None if allowed."""
    for reason, pattern in BLOCK_REASON_BY_PATTERN:
        if pattern.search(command):
            return reason
    return None


def append_block_log(command: str, project_path: str, reason: str) -> None:
    """Log blocked command attempt with timestamp, command, and project path."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "attempted_command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def denial_response(reason: str, command: str) -> dict[str, Any]:
    """Build Claude Code JSON hook response that denies the tool call."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked dangerous Bash command: "
                f"{reason}. Review the command before retrying. Command: {command}"
            ),
        }
    }


def main() -> int:
    event = load_event()
    command = command_from_event(event)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project_path = project_path_from_event(event)
    append_block_log(command, project_path, reason)
    print(json.dumps(denial_response(reason, command)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
