#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


BLOCK_PATTERNS = (
    (
        "rm -rf",
        re.compile(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b"),
        "Recursive force delete can permanently remove files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "Dropping a table is destructive and should be reviewed manually.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b", re.IGNORECASE),
        "Force-pushing can overwrite remote history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE removes data without row-by-row safeguards.",
    ),
)

DELETE_FROM_PATTERN = re.compile(r"\bdelete\s+from\b(?P<body>.*?)(?:;|$)", re.IGNORECASE | re.DOTALL)


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        deny(f"Could not parse hook input JSON: {exc}", command="<invalid-json>", project_path=os.getcwd())
        raise SystemExit(0)

    if isinstance(payload, dict):
        return payload
    return {}


def get_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
        if isinstance(command, str):
            return command
    return ""


def get_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "project_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def find_block_reason(command: str) -> str | None:
    for name, pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return f"{name}: {reason}"

    for match in DELETE_FROM_PATTERN.finditer(command):
        if not re.search(r"\bwhere\b", match.group("body"), re.IGNORECASE):
            return "DELETE FROM without WHERE: add a WHERE clause or run the command manually."

    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    home = Path(os.environ.get("HOME") or str(Path.home()))
    log_path = home / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str, command: str, project_path: str) -> None:
    log_block(command, project_path, reason)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked dangerous Bash command. "
                        f"{reason} Attempted command: {command!r}. "
                        "This attempt was logged to ~/.claude/hooks/blocked.log."
                    ),
                }
            }
        )
    )


def main() -> int:
    payload = load_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    command = get_command(payload)
    reason = find_block_reason(command)
    if not reason:
        return 0

    deny(reason, command=command, project_path=get_project_path(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
