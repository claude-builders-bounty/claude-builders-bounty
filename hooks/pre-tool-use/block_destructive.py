#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands

This hook intercepts tool use requests and blocks dangerous bash commands.
Blocked patterns:
  - rm -rf
  - DROP TABLE
  - git push --force
  - TRUNCATE
  - DELETE FROM without WHERE clause

Logs all blocked attempts to ~/.claude/hooks/blocked.log
"""

import sys
import json
import re
import os
from datetime import datetime

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
BLOCKED_LOG = os.path.join(HOOKS_DIR, "blocked.log")

# Destructive patterns to block
DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-rf\b', "rm -rf (recursive force delete)"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE"),
    (r'\bgit\s+push\s+--force\b', "git push --force"),
    (r'\bTRUNCATE\b', "TRUNCATE"),
]

# Pattern for DELETE FROM without WHERE
DELETE_NO_WHERE_PATTERN = r'\bDELETE\s+FROM\b(?!\s+WHERE)'


def is_destructive_command(command: str) -> tuple[bool, str]:
    """Check if command contains destructive patterns. Returns (is_blocked, reason)."""
    cmd_lower = command.lower()
    
    # Check each destructive pattern
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return True, description
    
    # Check DELETE FROM without WHERE
    if re.search(DELETE_NO_WHERE_PATTERN, command, re.IGNORECASE):
        return True, "DELETE FROM without WHERE clause"
    
    return False, ""


def log_blocked_attempt(command: str, reason: str) -> None:
    """Log blocked attempt to blocked.log with timestamp, user, and command."""
    timestamp = datetime.now().isoformat()
    user = os.environ.get("USER", "unknown")
    log_entry = f"[{timestamp}] user={user} blocked={reason} command={command}\n"
    
    # Ensure hooks directory exists
    os.makedirs(HOOKS_DIR, exist_ok=True)
    
    with open(BLOCKED_LOG, "a") as f:
        f.write(log_entry)


def main():
    """Main hook entry point. Reads JSON from stdin, returns modified or original input."""
    try:
        # Read Claude Code hook input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse input, allow it to pass through
        sys.exit(0)
    
    # Get the tool being used (tool_use or bash)
    tool = input_data.get("tool", "")
    
    # Only process bash commands
    if tool not in ("bash", "tool_use"):
        sys.exit(0)
    
    # Get the command to execute
    if tool == "bash":
        command = input_data.get("command", "")
    elif tool == "tool_use":
        # For tool_use, check the action
        action = input_data.get("action", "")
        if action == "bash":
            command = input_data.get("command", "")
        else:
            sys.exit(0)
    else:
        sys.exit(0)
    
    # Check for destructive commands
    is_blocked, reason = is_destructive_command(command)
    
    if is_blocked:
        # Log the blocked attempt
        log_blocked_attempt(command, reason)
        
        # Return a blocking response
        # This format tells Claude Code to reject the tool use
        error_response = {
            "error": f"BLOCKED: {reason}",
            "command": command,
            "message": f"Hook blocked destructive command: {reason}\nCommand: {command}\nThis has been logged."
        }
        print(json.dumps(error_response))
        sys.exit(1)
    
    # Command is safe, exit normally (no output = allow)
    sys.exit(0)


if __name__ == "__main__":
    main()