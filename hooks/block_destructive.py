#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    (r"\brm\s+(-[^\s]*)?-r([^\s]*)?\s+-([^\s]*)?f", "rm -rf (recursive force delete)"),
    (r"\brm\s+(-[^\s]*)?-f([^\s]*)?\s+-([^\s]*)?r", "rm -rf (recursive force delete)"),
    (r"\brm\s+-rf\b", "rm -rf (recursive force delete)"),
    (r"\brm\s+-fr\b", "rm -rf (recursive force delete)"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE (destructive SQL)"),
    (r"\bTRUNCATE\b", "TRUNCATE (destructive SQL)"),
    (r"\bgit\s+push\s+--force\b", "git push --force (force push)"),
    (r"\bgit\s+push\s+-f\b", "git push --force (force push)"),
    (r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any blocked pattern.

    Returns (blocked, reason) tuple.
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def log_blocked(command: str, reason: str) -> None:
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project_path = os.getcwd()
    entry = f"[{timestamp}] BLOCKED: {reason} | command: {command} | project: {project_path}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def main() -> None:
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        output = json.dumps({"decision": "approve"})
        print(output)
        return

    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        output = json.dumps({"decision": "approve"})
        print(output)
        return

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason)
        output = json.dumps({
            "decision": "block",
            "reason": f"BLOCKED: {reason}. This command was prevented by the destructive command guard hook. Please use a safer alternative.",
        })
        print(output)
    else:
        output = json.dumps({"decision": "approve"})
        print(output)


if __name__ == "__main__":
    main()
