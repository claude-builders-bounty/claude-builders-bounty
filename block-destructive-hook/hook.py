#!/usr/bin/env python3
"""
pre-tool-use hook: blocks destructive bash commands before execution.
Install to: ~/.claude/hooks/pre-tool-use

Usage:
  python3 pre-tool-use.py <tool_name> <tool_input_json>

The hook reads JSON from stdin (Claude Code passes tool call info).
Returns 0 to allow the tool, non-zero to block.
"""

import sys
import json
import re
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are ALWAYS blocked (case-insensitive)
BLOCKED_PATTERNS = [
    (r'rm\s+-rf\s+/', "Attempted to delete root filesystem"),
    (r'rm\s+-rf\s+\$HOME', "Attempted to delete home directory"),
    (r'rm\s+-rf\s+/home', "Attempted to delete /home"),
    (r'drop\s+table', "SQL DROP TABLE command"),
    (r'truncate\s+table', "SQL TRUNCATE TABLE command"),
    (r'delete\s+from\s+\w+\s*;?\s*$', "SQL DELETE without WHERE clause"),
    (r'--\s*;?\s*drop\s+table', "SQL comment injection with DROP"),
    (r'--\s*;?\s*truncate\s+table', "SQL comment injection with TRUNCATE"),
    (r'git\s+push\s+.*--force', "Force push to git remote"),
    (r'git\s+push\s+.*-f\s', "Force push to git remote (-f flag)"),
    (r'git\s+push\s+.*-f$', "Force push to git remote (-f flag)"),
    (r':\!\s*rm\s+-rf', "Shell history injection"),
    (r';\s*rm\s+-rf', "Chained delete command"),
    (r'&\&\s*rm\s+-rf', "Conditional delete command"),
]

# Commands that need extra scrutiny (warn but don't block)
WARN_PATTERNS = [
    r'rm\s+-rf',
    r'rm\s+-r',
    r'chmod\s+-R\s+777',
    r'chown\s+-R',
    r'delete\s+from',
    r'shutdown',
    r'reboot',
    r':\(',  # despair command
]


def log_blocked(timestamp, tool_name, command, project_path, reason):
    """Append blocked attempt to log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED | tool={tool_name} | project={project_path} | reason={reason}\n")
        f.write(f"  Command: {command[:200]}\n")
        f.write("-" * 80 + "\n")


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if command should be blocked.
    Returns (blocked: bool, reason: str).
    """
    cmd_lower = command.lower()

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return True, reason

    return False, ""


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No input — allow the tool
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only check bash tools
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Get project path from env or default
    project_path = os.environ.get("CLAUDE_PROJECT_PATH", os.getcwd())

    blocked, reason = check_command(command)

    if blocked:
        timestamp = datetime.now().isoformat()
        log_blocked(timestamp, tool_name, command, project_path, reason)

        # Print to stderr so Claude sees the message
        print(
            f"⛔ HOOK BLOCKED: {reason}\n"
            f"   Command: {command[:150]}{'...' if len(command) > 150 else ''}\n"
            f"   Project: {project_path}\n"
            f"   This command has been logged to: {LOG_FILE}\n"
            f"   If you believe this is a false positive, you can run it directly (bypassing the hook).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
