#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path


LOG_PATH = Path(os.environ.get("CLAUDE_BLOCK_LOG", Path.home() / ".claude" / "hooks" / "blocked.log"))

RULES = (
    (
        "rm -rf",
        re.compile(
            r"(^|[\s;&|()])rm\b(?=[^;&|()]*\s-[A-Za-z]*r)(?=[^;&|()]*\s-[A-Za-z]*f)",
            re.IGNORECASE,
        ),
        "Recursive forced remove commands are blocked.",
    ),
    (
        "rm --recursive --force",
        re.compile(r"(^|[\s;&|()])rm\b(?=.*\s--recursive\b)(?=.*\s--force\b)", re.DOTALL),
        "Recursive forced remove commands are blocked.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE is destructive and must be reviewed manually.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b(?=.*\s--force(?:\b|=)|.*\s-f\b)", re.IGNORECASE | re.DOTALL),
        "Force-pushing can rewrite shared history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE removes table data and must be reviewed manually.",
    ),
)


def _project_path(payload: dict) -> str:
    return (
        payload.get("cwd")
        or payload.get("project_dir")
        or payload.get("projectPath")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def _delete_from_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        match = re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE)
        if not match:
            continue
        tail = statement[match.end() :]
        if not re.search(r"\bwhere\b", tail, re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    for label, pattern, reason in RULES:
        if pattern.search(command):
            return f"Blocked `{label}`: {reason}"

    if _delete_from_without_where(command):
        return "Blocked `DELETE FROM` without a WHERE clause: this can delete every row in a table."

    return None


def _log_block(payload: dict, command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": _project_path(payload),
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    _log_block(payload, command, reason)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
