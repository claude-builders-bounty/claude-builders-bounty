#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.
Bounty: claude-builders-bounty #3
"""

import json
import sys
import os
import re
from datetime import datetime

# Patterns to block (severity: CRITICAL > HIGH > MEDIUM)
BLOCKED_PATTERNS = [
    (re.compile(r'rm\s+-rf', re.IGNORECASE), "CRITICAL", "Potentially destructive rm command"),
    (re.compile(r'DROP\s+TABLE', re.IGNORECASE), "CRITICAL", "SQL DROP TABLE command"),
    (re.compile(r'git\s+push\s+--force', re.IGNORECASE), "HIGH", "Force push can overwrite remote history"),
    (re.compile(r'TRUNCATE\s+', re.IGNORECASE), "CRITICAL", "SQL TRUNCATE command"),
    (re.compile(r'DELETE\s+FROM\s+\w+\s*$', re.IGNORECASE), "HIGH", "DELETE FROM without WHERE clause"),
]

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def check_command(command: str) -> dict:
    """Check if a command should be blocked."""
    for pattern, severity, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return {
                "allow": False,
                "severity": severity,
                "reason": reason,
                "command": command,
            }
    return {"allow": True, "message": "Command passed safety check"}


def log_blocked(command: str, severity: str, reason: str):
    """Log blocked command."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()
    log_entry = f"[{timestamp}] [{severity}] {reason}\n  Command: {command}\n  Path: {project_path}\n\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    result = check_command(command)

    if not result["allow"]:
        log_blocked(command, result["severity"], result["reason"])
        print(f"BLOCKED ({result['severity']}): {result['reason']}")
        print(json.dumps(result))
        sys.exit(1)
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
