#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Bounty: claude-builders-bounty/claude-builders-bounty #3 ($100)

This hook intercepts dangerous bash commands before execution.
It follows the Claude Code hooks format (~/.claude/hooks/).

Blocked patterns:
  - rm -rf (recursive force delete)
  - DROP TABLE (SQL destructive)
  - git push --force (force push)
  - TRUNCATE (SQL truncate)
  - DELETE FROM without WHERE clause (SQL untargeted delete)

Blocked attempts are logged to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


# Patterns that should be blocked
BLOCKED_PATTERNS = [
    # rm -rf variants
    re.compile(r"\brm\s+.*-[rRfFdD].*-[rRfFdD]", re.IGNORECASE),
    re.compile(r"\brm\s+-[rRfFdD]{2,}", re.IGNORECASE),
    re.compile(r"\brm\s+--recursive\s+--force", re.IGNORECASE),
    # DROP TABLE
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    # git push --force
    re.compile(r"\bgit\s+push\s+.*--force", re.IGNORECASE),
    re.compile(r"\bgit\s+push\s+-f\b", re.IGNORECASE),
    # TRUNCATE
    re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    # DELETE FROM without WHERE clause
    # Match DELETE FROM ... that does NOT contain WHERE anywhere after it
    re.compile(r"\bDELETE\s+FROM\s+\S+\s*;(?:\s|$)", re.IGNORECASE),
]


def log_blocked(attempted_command: str, project_path: str = ""):
    """Log a blocked attempt with timestamp, command, and project path."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] BLOCKED | cmd: {attempted_command} | path: {project_path}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def is_destructive(command: str) -> bool:
    """Check if a command matches any blocked pattern."""
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True
    return False


def main():
    """Main hook entry point. Reads Claude Code hook input from stdin."""
    # Claude Code hooks receive JSON input via stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # No valid input, allow the command
        sys.exit(0)

    # Extract the tool name and command
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("project_path", "")

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    if is_destructive(command):
        log_blocked(command, project_path)
        # Output a clear message explaining why the command was blocked
        reason = f"⛔ BLOCKED: The command '{command}' was identified as potentially destructive. "
        reason += "Destructive commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, "
        reason += "DELETE FROM without WHERE) are blocked to prevent accidental data loss. "
        reason += "If you really need to run this command, please confirm with the user first."
        print(reason, file=sys.stderr)
        # Exit with non-zero to signal Claude Code to block the command
        sys.exit(2)

    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()