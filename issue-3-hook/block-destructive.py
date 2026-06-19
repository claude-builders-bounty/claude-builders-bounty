#!/usr/bin/env python3
"""
Claude Code Pre-tool-use Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before execution and blocks them.
Logs every blocked attempt with timestamp, command, and project path.

Installation:
  cp block-destructive.py ~/.claude/hooks/block-destructive.py
  chmod +x ~/.claude/hooks/block-destructive.py

Then add to ~/.claude/hooks/settings.json:
  {
    "hooks": {
      "pre-tool-use": [
        {
          "matcher": "Bash",
          "command": "python3 ~/.claude/hooks/block-destructive.py"
        }
      ]
    }
  }

Or use the installer:
  python3 install.py
"""

import sys
import json
import os
import re
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    # rm -rf variants
    (r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|.*--force\s+).*", "rm -rf or rm --force detected"),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+.*", "rm -r (recursive delete) detected"),
    # SQL destructive commands
    (r"\bDROP\s+TABLE\b", "DROP TABLE detected"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE detected"),
    (r"\bTRUNCATE\s+", "TRUNCATE detected"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause detected"),
    # Git force push
    (r"\bgit\s+push\s+.*--force", "git push --force detected"),
    (r"\bgit\s+push\s+.*-f\b", "git push -f detected"),
    (r"\bgit\s+push\s+--force-with-lease", "git push --force-with-lease detected"),
    # Additional dangerous patterns
    (r"\bchmod\s+(-[a-zA-Z]*\s+)?777\b", "chmod 777 detected"),
    (r"\bmkfs\b", "mkfs (filesystem format) detected"),
    (r"\bdd\s+.*of=/dev/", "dd to device detected"),
    (r">\s*/dev/sd", "Write to block device detected"),
    (r"\bsudo\s+rm\s+", "sudo rm detected"),
    (r"\bsystemctl\s+(stop|disable|mask)\s+", "systemctl stop/disable/mask detected"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command: str, reason: str, project_path: str):
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "timestamp": timestamp,
            "command": command,
            "reason": reason,
            "project_path": project_path,
        }) + "\n")


def check_command(command: str) -> tuple:
    """
    Check if a command matches any blocked pattern.
    Returns (is_blocked, reason) tuple.
    """
    normalized = command.strip()

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, reason

    return False, ""


def main():
    # Read the hook input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = os.getcwd()

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_path)
        print(f"BLOCKED: {reason}")
        print(f"Command: {command}")
        print("This command was blocked for safety. If you truly need to run it,")
        print("consider a safer alternative or run it directly in your terminal.")
        sys.exit(2)


if __name__ == "__main__":
    main()
