#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks dangerous bash commands.

Installation:
  mkdir -p ~/.claude/hooks && cp claude-hook.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py

Usage:
  Automatically intercepts dangerous commands before execution.
  Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Patterns that indicate dangerous commands
DANGEROUS_PATTERNS = [
    # Recursive delete
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)\s', 'Recursive delete detected (rm -rf). This can permanently delete files.'),
    (r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*|--force)\s.*(-[a-zA-Z]*r[a-zA-Z]*|--recursive)', 'Recursive force delete detected.'),

    # Database destruction
    (r'\bDROP\s+TABLE\b', 'DROP TABLE detected. This permanently deletes a table and all its data.'),
    (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE detected. This permanently deletes all rows from a table.'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE without WHERE clause detected. This will delete ALL rows.'),

    # Git destruction
    (r'\bgit\s+push\s+.*--force\b', 'Force push detected. This can overwrite remote history and cause data loss.'),
    (r'\bgit\s+push\s+.*-f\b', 'Force push detected (-f flag). This can overwrite remote history.'),

    # System destruction
    (r'\bmkfs\b', 'Filesystem formatting detected. This will destroy all data on the target device.'),
    (r'\bdd\s+.*of=/dev/', 'Direct disk write detected. This can overwrite system data.'),

    # Permission changes
    (r'\bchmod\s+(-[a-zA-Z]*777[a-zA-Z]*|777)\s', 'chmod 777 detected. This grants full permissions to all users.'),
    (r'\bchmod\s+-R\s+777\s', 'Recursive chmod 777 detected. This grants full permissions to all files.'),

    # Dangerous network
    (r'\bcurl\s+.*\|\s*(bash|sh)\s', 'Piping curl to shell detected. This executes arbitrary remote code.'),
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(command: str, reason: str, project_path: str) -> None:
    """Log blocked command attempt."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {command[:200]}\n  Reason: {reason}\n  Project: {project_path}\n\n"

    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def check_command(tool_input: dict) -> tuple[bool, str]:
    """
    Check if a command is dangerous.

    Returns:
        (is_blocked, reason) tuple
    """
    command = tool_input.get("command", "")

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason

    return False, ""


def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Extract tool info
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check bash commands
    if tool_name not in ("Bash", "bash"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Get project path
    project_path = os.getcwd()

    # Check if command is dangerous
    is_blocked, reason = check_command(tool_input)

    if is_blocked:
        log_blocked_attempt(command, reason, project_path)

        # Output rejection to Claude
        output = {
            "blocked": True,
            "reason": reason,
            "message": f"🚫 BLOCKED: {reason}\n\nThis command was intercepted by the security hook. If you need to run this command, you must:\n1. Explain why it's necessary\n2. Add safeguards (e.g., --dry-run, --interactive, specific paths)\n3. Get explicit user confirmation"
        }
        print(json.dumps(output))
        sys.exit(0)

    # Command is safe, let it proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
