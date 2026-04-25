#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.

Install:
    mkdir -p ~/.claude/hooks && cp hook.py ~/.claude/hooks/destructive_guard.py
    Add to ~/.claude/settings.json (see README.md)
"""
import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that should be blocked
BLOCKED_PATTERNS = [
    (r"\brm\s+-[^\s]*r[^\s]*f\b|\brm\s+-[^\s]*f[^\s]*r\b|\brm\s+--no-preserve-root",
     "recursive force remove (rm -rf)"),
    (r"\bDROP\s+TABLE\b",
     "DROP TABLE statement"),
    (r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b",
     "git force push"),
    (r"\bTRUNCATE\b",
     "TRUNCATE statement"),
    (r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)",
     "DELETE FROM without WHERE clause"),
]


def is_blocked(command: str) -> tuple[bool, str]:
    """Return (blocked, reason) for a bash command."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def log_blocked(command: str, reason: str, project: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  project: {project}\n")
        f.write(f"  command: {command}\n\n")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse input, allow the command through
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    blocked, reason = is_blocked(command)
    if not blocked:
        sys.exit(0)

    log_blocked(command, reason, project)

    # Output structured response that Claude Code reads
    response = {
        "decision": "block",
        "reason": (
            f"Blocked: {reason}. "
            f"This command pattern is flagged as potentially destructive. "
            f"Logged to {LOG_FILE}. "
            f"If you need to run this, ask the user to execute it manually."
        ),
    }
    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
