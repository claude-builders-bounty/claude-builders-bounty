#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash/SQL commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"rm\s+(-[^\s]*\s+)*-[^\s]*r[^\s]*f|rm\s+-[^\s]*rf", re.I),
     "Recursive force-delete (`rm -rf`) can destroy project files irreversibly."),
    (re.compile(r"\bgit\s+push\b[^\n;|&]*--force\b|\bgit\s+push\b[^\n;|&]*\s-f\b", re.I),
     "Force-push rewrites remote history and can delete teammates' commits."),
    (re.compile(r"\bDROP\s+TABLE\b", re.I),
     "`DROP TABLE` permanently removes database tables."),
    (re.compile(r"\bTRUNCATE\b", re.I),
     "`TRUNCATE` wipes table data and is difficult to recover from."),
    (re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b).)*$", re.I | re.S),
     "`DELETE FROM` without `WHERE` deletes every row in the table."),
]


def project_path() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        if command:
            return str(command)
    return json.dumps(tool_input)


def find_violation(command: str) -> str | None:
    normalized = command.strip()
    if not normalized:
        return None
    for pattern, reason in RULES:
        if pattern.search(normalized):
            return reason
    return None


def append_log(command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    line = (
        f"{timestamp}\tproject={project_path()}\t"
        f"command={command!r}\treason={reason}\n"
    )
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)


def deny(reason: str, command: str) -> None:
    append_log(command, reason)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked by destructive-command hook: {reason} "
                f"Attempted command: {command}"
            ),
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        return

    command = extract_command(payload)
    reason = find_violation(command)
    if reason:
        deny(reason, command)


if __name__ == "__main__":
    main()
