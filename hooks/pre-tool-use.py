#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

This hook intercepts Bash tool calls before execution and blocks commands
matching known dangerous patterns (rm -rf, DROP TABLE, etc.).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Dangerous command patterns to block
# Each tuple: (compiled regex, pattern name, reason)
DANGEROUS_PATTERNS = [
    (
        re.compile(r'\brm\s+.*-[^\s]*r[^\s]*f|rm\s+.*-f[^\s]*r', re.IGNORECASE),
        "rm -rf",
        "Recursive forced deletion detected. This can permanently destroy files and directories.",
    ),
    (
        re.compile(r'\brm\s+--force\s+--recursive', re.IGNORECASE),
        "rm --force --recursive",
        "Recursive forced deletion detected. This can permanently destroy files and directories.",
    ),
    (
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        "DROP TABLE",
        "Database table deletion detected. This permanently removes table structure and all data.",
    ),
    (
        re.compile(r'\bgit\s+push\s+.*--force\b', re.IGNORECASE),
        "git push --force",
        "Force push detected. This rewrites remote history and can cause data loss for collaborators.",
    ),
    (
        re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
        "TRUNCATE",
        "Table truncation detected. This permanently removes all rows from a database table.",
    ),
    (
        re.compile(r'\bDELETE\s+FROM\b(?!\s+\S+\s+WHERE)', re.IGNORECASE),
        "DELETE FROM without WHERE",
        "Unconditional DELETE detected. DELETE FROM without a WHERE clause removes all rows from the table.",
    ),
]

# Path for logging blocked attempts
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def get_project_path() -> str:
    """Get the current project/working directory."""
    return os.environ.get("PWD", os.getcwd())


def log_blocked_attempt(command: str, pattern_name: str, reason: str) -> None:
    """Log a blocked command attempt to the log file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project_path = get_project_path()

    log_entry = (
        f"[{timestamp}] BLOCKED: {pattern_name}\n"
        f"  Command: {command}\n"
        f"  Project: {project_path}\n"
        f"  Reason:  {reason}\n"
        f"{'-' * 60}\n"
    )

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str, str]:
    """
    Check if a command matches any dangerous patterns.

    Returns:
        (is_blocked, pattern_name, reason) - pattern_name/reason are empty if not blocked
    """
    for pattern, name, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True, name, reason
    return False, "", ""


def main() -> None:
    """Main hook entry point."""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # If we can't parse input, allow the command (fail open for compatibility)
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")

    # Only check Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    # Extract the command from tool parameters
    tool_params = input_data.get("tool_parameters", {})
    command = tool_params.get("command", "")

    if not command:
        sys.exit(0)

    # Check against dangerous patterns
    is_blocked, pattern_name, reason = check_command(command)

    if is_blocked:
        log_blocked_attempt(command, pattern_name, reason)

        # Output blocking message to stderr (Claude sees this)
        error_msg = (
            f"🚫 COMMAND BLOCKED by security hook\n"
            f"\n"
            f"Pattern: {pattern_name}\n"
            f"Command: {command}\n"
            f"\n"
            f"Why: {reason}\n"
            f"\n"
            f"This command has been blocked to prevent potential data loss.\n"
            f"If this is intentional, you can:\n"
            f"  1. Run the command manually in your terminal\n"
            f"  2. Temporarily disable the hook: chmod -x ~/.claude/hooks/pre-tool-use.py\n"
            f"\n"
            f"Blocked attempt logged to: {LOG_PATH}\n"
        )
        print(error_msg, file=sys.stderr)
        # Exit code 2 = block the tool call
        sys.exit(2)

    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
