#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.
Install: cp block_destructive.py ~/.claude/hooks/
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Patterns that should be blocked
BLOCKED_PATTERNS = [
    # Filesystem destruction
    (r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+.*|.*-rf\b|.*-fr\b)', "rm -rf: recursive force delete"),
    (r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+[/~]', "rm -r on root or home directory"),
    # SQL destruction
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', "DROP TABLE/DATABASE/SCHEMA"),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', "TRUNCATE table"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?:;|\s*$)', "DELETE FROM without WHERE clause"),
    # Git destruction
    (r'\bgit\s+push\s+.*--force\b', "git push --force"),
    (r'\bgit\s+push\s+-f\b', "git push -f (force)"),
    (r'\bgit\s+clean\s+-[a-zA-Z]*f', "git clean -f (force remove untracked)"),
    (r'\bgit\s+reset\s+--hard\b', "git reset --hard"),
    # System destruction
    (r'\bmkfs\b', "mkfs: format filesystem"),
    (r'\bdd\s+.*of=/dev/', "dd writing to device"),
    (r'>\s*/dev/sd[a-z]', "redirect to block device"),
    (r'\bchmod\s+-R\s+777\s+/', "chmod -R 777 on root"),
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any blocked pattern.
    Returns (is_blocked, reason).
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Log blocked command attempt."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED: {reason} | Command: {command} | Project: {project_path}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def main():
    """Main hook entry point. Reads tool-use event from stdin."""
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, allow the command (fail open)
        sys.exit(0)

    # Extract the tool name and input
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Only check bash/shell tool calls
    if tool_name not in ("bash", "terminal", "shell", "execute_command"):
        sys.exit(0)

    # Get the command being executed
    command = tool_input.get("command", "") or tool_input.get("cmd", "")
    if not command:
        sys.exit(0)

    # Check against blocked patterns
    is_blocked, reason = check_command(command)

    if is_blocked:
        project_path = event.get("project_path", event.get("cwd", "unknown"))
        log_blocked(command, reason, project_path)

        # Output block message for Claude to see
        result = {
            "blocked": True,
            "message": (
                f"⛔ BLOCKED: {reason}\n"
                f"Command: {command}\n\n"
                "This command was blocked by the pre-tool-use safety hook because "
                "it matches a destructive pattern. If you believe this is a false "
                "positive, ask the user for explicit permission before proceeding."
            ),
        }
        print(json.dumps(result))
        sys.exit(1)  # Non-zero exit = block the tool use

    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
