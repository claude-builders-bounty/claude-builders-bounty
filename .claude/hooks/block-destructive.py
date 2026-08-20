#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""
import datetime
import json
import os
import re
import sys

PATTERNS = (
    (re.compile(r"\brm\s+(?:-[A-Za-z]*\s+)*-?rf\b", re.IGNORECASE), "rm -rf can recursively and permanently delete files"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE can permanently delete a database table"),
    (re.compile(r"\bgit\s+push\b[^\n]*\s(?:--force|-f)(?:\s|$)", re.IGNORECASE), "force-pushing can overwrite shared history"),
    (re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE), "TRUNCATE can permanently remove all rows from a table"),
)
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def log_block(command: str, project_path: str) -> None:
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"{timestamp}\t{project_path}\t{command}\n")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return

    command = str(payload.get("tool_input", {}).get("command", ""))
    project_path = str(payload.get("cwd") or os.getcwd())
    reason = None
    for pattern, explanation in PATTERNS:
        if pattern.search(command):
            reason = explanation
            break
    if reason is None and DELETE_FROM.search(command) and not WHERE.search(command):
        reason = "DELETE FROM without a WHERE clause can delete every row"

    if reason:
        log_block(command, project_path)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked destructive Bash command: {reason}. Review and narrow the command before retrying.",
            }
        }))


if __name__ == "__main__":
    main()
