#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Install:
    mkdir -p ~/.claude/hooks
    cp dangerous-command-hook.py ~/.claude/hooks/pre-tool-use.py
    chmod +x ~/.claude/hooks/pre-tool-use.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that indicate destructive commands
BLOCKED_PATTERNS = [
    (r"\brm\s+.*-r.*f\b", "rm -rf detected: recursive force deletion"),
    (r"\brm\s+.*-f.*r\b", "rm -rf detected: recursive force deletion"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE detected: destructive SQL"),
    (r"\bgit\s+push\s+.*--force\b", "git push --force detected: force push"),
    (r"\bgit\s+push\s+.*-f\b", "git push --force detected: force push"),
    (r"\bTRUNCATE\b", "TRUNCATE detected: destructive SQL"),
    (r"\bDELETE\s+FROM\b(?![\s\S]*?\bWHERE\b)", "DELETE FROM without WHERE detected"),
]


def log_blocked(timestamp: str, command: str, project_path: str, reason: str) -> None:
    """Append blocked attempt to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {command}\n")
        f.write(f"  Reason: {reason}\n")
        f.write(f"  Project: {project_path}\n\n")


def check_command(command: str) -> str | None:
    """Return reason if command matches a blocked pattern, else None."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return None


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    command = input_data.get("command", "")
    if not command:
        sys.exit(0)

    reason = check_command(command)
    if reason is None:
        sys.exit(0)

    # Log the blocked attempt
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project_path = os.getcwd()
    log_blocked(now, command, project_path, reason)

    # Output JSON response to Claude
    response = {
        "decision": "block",
        "reason": (
            f"⛔ Command blocked by safety hook.\n\n"
            f"Reason: {reason}\n"
            f"Command: {command}\n\n"
            f"This command was intercepted because it could cause "
            f"irreversible damage. If you believe this is a mistake, "
            f"ask the user to run it manually outside of Claude Code."
        ),
    }
    print(json.dumps(response))


if __name__ == "__main__":
    main()