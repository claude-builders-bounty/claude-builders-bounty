#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# rm with recursive + force in any flag order/combo (e.g. rm -rf, rm -fr, rm -r -f)
# Allows leading env/sudo tokens before rm within a shell statement.
RM_RF = re.compile(
    r"(?:^|[;&|()\n]|&&|\|\|)\s*(?:[A-Za-z_][\w]*=\S*\s+|sudo\s+)*rm\s+"
    r"(?=[^\n;&|]*-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r|"
    r"[a-zA-Z]*r\b[^\n;&|]*-[a-zA-Z]*f|[a-zA-Z]*f\b[^\n;&|]*-[a-zA-Z]*r))",
    re.IGNORECASE,
)

DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
# SQL TRUNCATE (avoid the Unix truncate(1) utility: truncate -s / truncate --size)
TRUNCATE = re.compile(
    r"\bTRUNCATE\s+TABLE\b"
    r"|\bTRUNCATE\s+(?!-)(?:ONLY\s+)?(?:\w+\.)?(?:[`\"]?\w+[`\"]?)",
    re.IGNORECASE,
)

# git push --force / -f / --force-with-lease (force push family)
GIT_FORCE_PUSH = re.compile(
    r"\bgit\s+push\b[^\n]*?(?:--force(?:-with-lease)?\b|(?<=\s)-f\b)",
    re.IGNORECASE,
)

# DELETE FROM ... with no WHERE clause before statement end
DELETE_NO_WHERE = re.compile(
    r"\bDELETE\s+FROM\b(?![^\n;]*\bWHERE\b)",
    re.IGNORECASE,
)


def find_block_reason(command: str) -> Optional[str]:
    if RM_RF.search(command):
        return (
            "Blocked destructive command: `rm -rf` (recursive force delete). "
            "Use a safer, more targeted removal instead."
        )
    if DROP_TABLE.search(command):
        return (
            "Blocked destructive SQL: `DROP TABLE`. "
            "This permanently destroys table schema and data."
        )
    if TRUNCATE.search(command):
        return (
            "Blocked destructive SQL: `TRUNCATE`. "
            "This empties a table without a WHERE filter."
        )
    if GIT_FORCE_PUSH.search(command):
        return (
            "Blocked destructive git command: `git push --force` "
            "(or equivalent force push). Force-pushing rewrites remote history."
        )
    if DELETE_NO_WHERE.search(command):
        return (
            "Blocked destructive SQL: `DELETE FROM` without a `WHERE` clause. "
            "Add a WHERE condition or use an explicit, reviewed bulk-delete path."
        )
    return None


def log_blocked(command: str, project_path: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Single-line log entry: timestamp, command, project path
    safe_cmd = command.replace("\n", "\\n")
    line = f"{timestamp}\t{safe_cmd}\t{project_path}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return 0

    tool_name = data.get("tool_name") or data.get("tool") or ""
    if tool_name and tool_name != "Bash":
        return 0

    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = (
        data.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    try:
        log_blocked(command, str(project_path))
    except OSError:
        pass

    deny(reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
