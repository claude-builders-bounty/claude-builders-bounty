#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code.
Blocks dangerous bash commands before execution.

Install:
  mkdir -p ~/.claude/hooks
  cp dangerous_commands.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/dangerous_commands.py

Configure in ~/.claude/settings.json:
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/dangerous_commands.py" }]
        }
      ]
    }
  }
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    (r'\brm\s+-rf?\b', "rm -rf: recursive force delete"),
    (r'\brm\s+(-\w*f\w*|-\w*r\w*){2}', "rm with -rf flags"),
    (r'DROP\s+TABLE', "SQL DROP TABLE"),
    (r'TRUNCATE\s+(?:TABLE\s+)?\w+', "SQL TRUNCATE"),
    (r'DELETE\s+FROM\s+\w+\s*(?:;|$)', "DELETE FROM without WHERE clause"),
    (r'git\s+push\s+.*--force(?:-with-lease)?', "git push --force"),
    (r'git\s+push\s+-f\b', "git push -f"),
    (r':\s*>\s*/', "redirect to root path"),
    (r'mkfs\b', "mkfs: format filesystem"),
    (r'dd\s+if=.*of=/dev/', "dd writing to device"),
]

def log_blocked(command: str, reason: str, project_path: str):
    """Log blocked command to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked pattern. Returns (is_blocked, reason)."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON input, allow through
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only process Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = os.getcwd()
    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_path)
        # Output block message for Claude to see
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"🚫 Blocked: {reason}\n"
                f"Command: `{command}`\n"
                f"This command has been logged to {LOG_FILE}\n"
                f"If you need to run this, please ask the user to execute it manually."
            )
        }))
        sys.exit(0)

    # Allow the command
    sys.exit(0)

if __name__ == "__main__":
    main()
