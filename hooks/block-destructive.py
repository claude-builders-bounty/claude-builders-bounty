#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands
Blocks dangerous bash commands before they execute.
Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path

# Patterns to block (case-insensitive)
BLOCKED_PATTERNS = [
    (r'\brm\s+-[a-z]*r[a-z]*f[a-z]*',       "rm -rf: recursively force-delete files/directories"),
    (r'\brm\s+-[a-z]*f[a-z]*r[a-z]*',       "rm -fr: recursively force-delete files/directories"),
    (r'\brm\s+--recursive\s+--force',        "rm --recursive --force: recursively force-delete"),
    (r'\bDROP\s+TABLE\b',                    "DROP TABLE: permanently deletes a database table"),
    (r'\bgit\s+push\s+.*--force\b',          "git push --force: overwrites remote history"),
    (r'\bgit\s+push\s+.*-f\b(?!.*--force)',  "git push -f: overwrites remote history"),
    (r'\bTRUNCATE\b',                        "TRUNCATE: removes all rows from a table"),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',    "DELETE FROM without WHERE: deletes all rows in a table"),
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command: str, reason: str):
    """Log blocked attempt to file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  Command: {command}\n")
        f.write(f"  Project: {project_path}\n\n")


def check_command(command: str) -> str | None:
    """Check if command matches any blocked pattern. Returns reason or None."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return None


def main():
    try:
        tool_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Can't parse — don't block

    # Only check Bash tool calls
    if tool_input.get("tool_name") != "Bash":
        sys.exit(0)

    command = tool_input.get("tool_input", {}).get("command", "")
    reason = check_command(command)

    if reason:
        log_blocked(command, reason)
        response = {
            "decision": "block",
            "reason": (
                f"🚫 Command blocked by safety hook.\n\n"
                f"**Why:** {reason}\n"
                f"**Command:** `{command}`\n\n"
                f"This command was not executed. If this is intentional and safe, "
                f"run it manually in your terminal.\n\n"
                f"Logged to: `{LOG_PATH}`"
            )
        }
        print(json.dumps(response))
    # No output = approve


if __name__ == "__main__":
    main()
