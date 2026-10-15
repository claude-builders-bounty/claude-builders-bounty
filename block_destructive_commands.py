#!/usr/bin/env python3
"""Claude Code PreToolUse hook blocking destructive Bash commands."""

import datetime
import json
import os
import re
import sys
from pathlib import Path


def block_reason(command: str) -> str | None:
    patterns = (
        (r"\brm\s+-[^\n;|&]*r[^\n;|&]*f\b|\brm\s+-[^\n;|&]*f[^\n;|&]*r\b", "recursive forced removal (rm -rf)"),
        (r"\bDROP\s+TABLE\b", "DROP TABLE can permanently remove a table"),
        (r"\bgit\s+push\b[^\n;|&]*(?:--force(?:-with-lease)?|-f)(?:\s|$)", "forced git push can overwrite remote history"),
        (r"\bTRUNCATE(?:\s+TABLE)?\b", "TRUNCATE can permanently remove table data"),
    )
    for pattern, reason in patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return reason

    for statement in re.split(r"[;\n]", command):
        if re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE) and not re.search(
            r"\bWHERE\b", statement, re.IGNORECASE
        ):
            return "DELETE FROM without a WHERE clause can remove every row"
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    command = event.get("tool_input", {}).get("command", "")
    if not isinstance(command, str):
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    project = event.get("cwd") or os.getcwd()
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps({"timestamp": timestamp, "command": command, "project_path": project}) + "\n")

    message = f"Blocked destructive Bash command: {reason}. Review and use a safer, explicitly scoped command."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": message}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
