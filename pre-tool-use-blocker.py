#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook — Block Destructive Commands
Intercepts dangerous bash/SQL commands before execution.

Installation:
  1. cp pre-tool-use-blocker.py ~/.claude/hooks/
  2. chmod +x ~/.claude/hooks/pre-tool-use-blocker.py

Reads tool call stdin JSON, checks for destructive patterns, blocks if dangerous.
"""

import json
import sys
import os
import re
from datetime import datetime

HOOK_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")

# Patterns that will be blocked
DESTRUCTIVE_PATTERNS = [
    (r"\brm\s+-rf\b", "rm -rf", "Recursively deletes files without confirmation"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE", "Irreversibly drops a database table and all its data"),
    (r"\bgit\s+push\s+--force\b", "git push --force", "Force-pushes, potentially overwriting remote history"),
    (r"\bgit\s+push\s+-f\b", "git push -f", "Force-pushes (short form), potentially overwriting remote history"),
    (r"\bTRUNCATE\b", "TRUNCATE", "Removes all rows from a table without WHERE clause"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM (no WHERE)", "Deletes all rows from a table — missing WHERE clause"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE", "Irreversibly drops an entire database"),
    (r"\b:(){ :|:& };:", "fork bomb", "Shell fork bomb — can crash the system"),
    (r"\bchmod\s+777\b", "chmod 777", "Grants world-writable permissions — security risk"),
    (r"\bdd\s+if=.*of=/dev/", "dd to /dev", "Raw write to device — can corrupt disks"),
]


def log_block(command: str, reason: str, project_path: str = ""):
    """Log blocked command to file"""
    os.makedirs(HOOK_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "reason": reason,
        "project": project_path or os.getcwd(),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # No input — pass through (not a tool call hook invocation)
        print("{}")
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only intercept bash commands
    if tool_name not in ("Bash", "bash", "run_shell_command", "execute_command"):
        print(json.dumps(input_data))
        return 0

    command = tool_input.get("command", "") or tool_input.get("cmd", "") or str(tool_input)
    command_normalized = " ".join(command.split())

    for pattern, name, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command_normalized, re.IGNORECASE):
            # Log the attempt
            log_block(command_normalized, name, os.getcwd())

            # Return a clear blocking message
            result = {
                "continue": False,
                "hookSpecificOutput": {
                    "hookEventName": "pre-tool-use",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"⚠️  BLOCKED: {name}\n"
                        f"Reason: {reason}\n"
                        f"\nThis command has been intercepted by the safety hook.\n"
                        f"Logged to: {LOG_FILE}\n"
                        f"\nIf you are certain this is safe, you can bypass the hook by temporarily disabling it."
                    ),
                },
            }
            print(json.dumps(result))
            return 0

    # Command is safe — pass through
    print(json.dumps(input_data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
