#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code
Blocks dangerous bash commands before they are executed.

Install: ~/.claude/hooks/pre_tool_use.py
Docs: https://docs.anthropic.com/claude-code/hooks

Claude Code passes tool input as JSON on stdin.
Exit 0   → allow
Exit 2   → block (with explanation on stdout for Claude)
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

# Path for the blocked commands log
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# -------------------------------------------------------------------
# Dangerous patterns to block
# Each entry: (pattern_regex, human_readable_description)
# -------------------------------------------------------------------
BLOCKED_PATTERNS = [
    # rm -rf (any variant with -r/-R/-f in any order, with or without sudo)
    (
        r"(?:sudo\s+)?rm\s+(?:\S+\s+)*-[rRfF]*[rR][rRfF]*\s",
        "Recursive force-remove (rm -rf): could permanently delete critical files",
    ),
    (
        r"(?:sudo\s+)?rm\s+-[rRfF]*[rR][rRfF]*\s",
        "Recursive force-remove (rm -rf): could permanently delete critical files",
    ),
    # DROP TABLE
    (
        r"\bDROP\s+TABLE\b",
        "DROP TABLE: irreversible database table deletion",
    ),
    # TRUNCATE
    (
        r"\bTRUNCATE\b",
        "TRUNCATE: deletes all rows from a table without WHERE clause",
    ),
    # DELETE FROM without WHERE (catches both plain SQL and SQL in shell strings)
    (
        r"\bDELETE\s+FROM\s+[\w.`\"'\[\]]+\s*(?:;|\"|'|$)",
        "DELETE FROM without WHERE clause: deletes every row in the table",
    ),
    # git push --force (any variant: -f, --force, --force-with-lease)
    (
        r"\bgit\s+push\b.*(?:--force|-f\b|--force-with-lease)",
        "git push --force: rewrites remote history, may cause data loss for other contributors",
    ),
    # Bonus: prevent piping /dev/null into critical files
    (
        r">\s*/etc/(?:passwd|shadow|sudoers|hosts)\b",
        "Overwriting critical system file: /etc/passwd, /etc/shadow, /etc/sudoers, or /etc/hosts",
    ),
    # Bonus: chmod 777 on sensitive paths
    (
        r"\bchmod\s+(?:777|a\+rwx)\s+/(?:etc|usr|bin|sbin|boot)\b",
        "chmod 777 on system directory: removes all permission restrictions",
    ),
]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked command entry to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Command: {command!r}\n"
        f"  Reason:  {reason}\n"
        f"  Project: {project_path}\n"
        f"  ---\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Returns (is_blocked, reason).
    Checks the command against all BLOCKED_PATTERNS.
    """
    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
            return True, description
    return False, ""


def main() -> None:
    # Read tool input from stdin
    try:
        raw = sys.stdin.read()
        tool_input = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # If we can't parse, let it through — don't break normal usage
        sys.exit(0)

    # We only care about Bash tool calls
    tool_name = tool_input.get("tool_name", "")
    if tool_name not in ("Bash", "bash", "shell"):
        sys.exit(0)

    # Extract the command
    tool_params = tool_input.get("tool_input", tool_input)
    command = tool_params.get("command", "")
    if not command:
        sys.exit(0)

    # Get project path for logging
    project_path = os.getcwd()

    # Check against blocked patterns
    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_path)

        # Output a clear explanation for Claude Code (shown to Claude)
        message = (
            f"🚫 COMMAND BLOCKED by pre-tool-use safety hook\n\n"
            f"Command: {command!r}\n\n"
            f"Reason: {reason}\n\n"
            f"This command was blocked to prevent irreversible damage. "
            f"If you genuinely need to run this command:\n"
            f"  1. Ask the user to confirm they understand the risks\n"
            f"  2. Suggest a safer alternative if one exists\n"
            f"  3. The block has been logged to: {LOG_FILE}\n\n"
            f"Do NOT attempt to work around this hook."
        )
        print(message)
        sys.exit(2)  # Exit code 2 = block in Claude Code hooks

    # Command is safe — allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
