#!/usr/bin/env python3
"""Claude Code Pre-Tool-Use Hook: Blocks destructive bash commands.

Installed at ~/.claude/hooks/pre-tool-use.py
Intercepts tool calls before execution and blocks dangerous patterns.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    {
        "pattern": re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|(-[a-zA-Z]*f[a-zA-Z]*r))\b|\brm\s+-rf\b", re.IGNORECASE),
        "description": "Recursive force delete (rm -rf)",
    },
    {
        "pattern": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "description": "SQL DROP TABLE",
    },
    {
        "pattern": re.compile(r"\bgit\s+push\s+--force\b|\bgit\s+push\s+-f\b", re.IGNORECASE),
        "description": "Git force push",
    },
    {
        "pattern": re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "description": "SQL TRUNCATE",
    },
    {
        "pattern": re.compile(
            r"\bDELETE\s+FROM\s+\S+\s*(?:;|$|\n)", re.IGNORECASE
        ),
        "description": "DELETE FROM without WHERE clause",
    },
]


def get_log_path() -> str:
    """Return the path to the blocked commands log file."""
    hooks_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    return os.path.join(hooks_dir, "blocked.log")


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Log a blocked command attempt to blocked.log."""
    log_path = get_log_path()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Command: {command}\n"
        f"  Reason: {reason}\n"
        f"  Project: {project_path}\n\n"
    )
    with open(log_path, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any blocked pattern.
    
    Returns (is_blocked, reason).
    """
    for entry in BLOCKED_PATTERNS:
        if entry["pattern"].search(command):
            return True, entry["description"]
    return False, ""


def main() -> None:
    """Main hook entry point. Reads tool input from stdin per Claude Code hooks spec."""
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, allow the command (fail open for non-bash)
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept bash/shell tool calls
    if tool_name not in ("Bash", "bash", "execute", "shell", "terminal"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Get project path from environment or hook input
    project_path = hook_input.get("project_path", os.getcwd())

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_path)
        # Output error message for Claude to see
        result = {
            "decision": "block",
            "reason": (
                f"🛑 BLOCKED: {reason}\n"
                f"The command `{command[:100]}` was blocked by the pre-tool-use security hook.\n"
                f"This pattern is considered destructive and has been prevented from executing.\n"
                f"The attempt has been logged to ~/.claude/hooks/blocked.log\n"
                f"Please use a safer alternative."
            ),
        }
        print(json.dumps(result))
        sys.exit(2)

    # Command is safe — allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
