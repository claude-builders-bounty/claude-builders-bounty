#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Receives JSON on stdin from Claude Code with tool_name, tool_input, and project_path.
Exits 0 to allow, exits 2 with reason on stdout to block.
Logs all blocked attempts to ~/.claude/hooks/blocked.log.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Each entry: (compiled regex, human-readable reason)
DESTRUCTIVE_PATTERNS = [
    (
        re.compile(r"\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\b"),
        "rm -rf (recursive force delete)",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE (destructive database operation)",
    ),
    (
        re.compile(r"\bgit\s+push\b[^|;&]*?(--force\b|\s-f\b)"),
        "git push --force (overwrites remote history)",
    ),
    (
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE (removes all data from table)",
    ),
]


def check_delete_without_where(command):
    """Return True if command contains DELETE FROM without a WHERE clause."""
    return bool(
        re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE)
        and not re.search(r"\bWHERE\b", command, re.IGNORECASE)
    )


def log_blocked(command, project_path, reason):
    """Append a blocked-command entry to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_FILE, "a") as f:
        f.write(
            f"[{timestamp}] BLOCKED | project: {project_path} "
            f"| reason: {reason} | command: {command}\n"
        )


def block(command, reason):
    """Print denial message and exit with code 2 to block the tool call."""
    print(
        f"BLOCKED: {reason}\n"
        f"Command: {command}\n\n"
        f"This command was blocked by the destructive command guard hook.\n"
        f"If this was intentional, temporarily disable the hook in "
        f"~/.claude/settings.json under hooks.PreToolUse."
    )
    sys.exit(2)


def main():
    # Parse hook input from stdin
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    # Only inspect Bash tool calls
    if data.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    project_path = data.get("project_path", os.getcwd())

    if not command:
        sys.exit(0)

    # Check each destructive pattern
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            log_blocked(command, project_path, reason)
            block(command, reason)

    # Special case: DELETE FROM without WHERE
    if check_delete_without_where(command):
        reason = "DELETE FROM without WHERE clause (would delete all rows)"
        log_blocked(command, project_path, reason)
        block(command, reason)

    # Command is safe — allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
