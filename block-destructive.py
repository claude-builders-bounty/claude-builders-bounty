#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before execution and blocks them.
Logs every blocked attempt to ~/.claude/hooks/blocked.log

Blocked patterns:
  - rm -rf / rm -r
  - DROP TABLE
  - TRUNCATE
  - DELETE FROM without WHERE clause
  - git push --force / git push -f
  - git push --force-with-lease

Installation:
  cp block-destructive.py ~/.claude/hooks/block-destructive.py
  chmod +x ~/.claude/hooks/block-destructive.py

  Then add to ~/.claude/settings.json:
  {
    "hooks": {
      "preToolUse": [
        {
          "type": "command",
          "command": "python3 ~/.claude/hooks/block-destructive.py",
          "matcher": "Bash"
        }
      ]
    }
  }
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# Destructive patterns to block (case-insensitive)
BLOCKED_PATTERNS = [
    # rm -rf / rm -r
    (r'\brm\s+.*-(?:r|rf|fr|R)\b', 'rm -rf: Recursive force delete is blocked'),
    (r'\brm\s+-.*r\b', 'rm -r: Recursive delete is blocked'),
    # DROP TABLE
    (r'\bDROP\s+TABLE\b', 'DROP TABLE: Dropping tables is blocked'),
    # TRUNCATE
    (r'\bTRUNCATE\s+', 'TRUNCATE: Truncating tables is blocked'),
    # DELETE FROM without WHERE
    (r'\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)', 'DELETE FROM without WHERE: Unconditional deletes are blocked'),
    # git push --force / -f
    (r'\bgit\s+push\s+.*--force', 'git push --force: Force pushing is blocked'),
    (r'\bgit\s+push\s+.*\s-f\b', 'git push -f: Force pushing is blocked'),
    (r'\bgit\s+push\s+-f\b', 'git push -f: Force pushing is blocked'),
    (r'\bgit\s+push\s+--force-with-lease', 'git push --force-with-lease: Force pushing is blocked'),
]


def get_log_path():
    """Get the log file path"""
    home = Path.home()
    hooks_dir = home / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "blocked.log"


def log_blocked(command: str, reason: str, project_path: str = ""):
    """Log a blocked command attempt"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n\n"
    log_path = get_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command contains destructive patterns.
    Returns (is_blocked, reason).
    """
    # Normalize for matching
    cmd_upper = command.upper()
    cmd_combined = command  # Keep original case for regex

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_combined, re.IGNORECASE):
            return True, reason

    return False, ""


def main():
    # Read hook input from stdin (Claude Code sends JSON)
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # No valid input, allow the command
        sys.exit(0)

    # Extract the bash command from the hook input
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    # Get project path if available
    project_path = input_data.get("cwd", os.getcwd())

    # Check for destructive patterns
    is_blocked, reason = check_command(command)

    if is_blocked:
        # Log the blocked attempt
        log_blocked(command, reason, project_path)

        # Output JSON to tell Claude why it was blocked
        response = {
            "decision": "block",
            "reason": f"⛔ Blocked: {reason}. This command was intercepted by the safety hook. The attempt has been logged to ~/.claude/hooks/blocked.log"
        }
        print(json.dumps(response))
        sys.exit(0)
    else:
        # Allow the command
        sys.exit(0)


if __name__ == "__main__":
    main()
