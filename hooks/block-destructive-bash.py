#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _load_event() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _project_path(event: dict) -> str:
    return (
        event.get("cwd")
        or event.get("project_dir")
        or event.get("workspace")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def _delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        tail = command[match.end():]
        statement = tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def _block_reason(command: str) -> str | None:
    checks = [
        (r"\brm\s+-(?=[^\s;]*r)(?=[^\s;]*f)[^\s;]*\b", "rm -rf recursively deletes files"),
        (r"\bdrop\s+table\b", "DROP TABLE removes an entire database table"),
        (r"\bgit\s+push\b[^\n;]*\s--force(?:\b|=)", "git push --force can overwrite remote history"),
        (r"\btruncate\b", "TRUNCATE removes table data without row-by-row safeguards"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return reason
    if _delete_without_where(command):
        return "DELETE FROM without a WHERE clause can remove every row"
    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={safe_command}\n")


def main() -> int:
    event = _load_event()
    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    reason = _block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(event)
    _log_block(command, project_path, reason)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: " + reason +
                ". The attempted command was logged to ~/.claude/hooks/blocked.log."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
