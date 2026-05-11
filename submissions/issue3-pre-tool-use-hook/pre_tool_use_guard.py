#!/usr/bin/env python3
"""
Pre-tool-use hook: blocks destructive bash commands before execution.
Follows Claude Code hooks format. Install to ~/.claude/hooks/
"""
import json
import re
import sys
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Each entry: (pattern, reason, flags)
# SQL patterns use a negative-lookahead approach:
#   block bare SQL statements but not when they appear inside single/double quotes
#   (i.e., as arguments to grep, echo, etc.)
DESTRUCTIVE_PATTERNS = [
    (r"\brm\s+(-\w*\s+)*-[rR][fF]\b", "rm -rf: recursive force deletion", 0),
    (r"\brm\s+(-\w*\s+)*-[fF][rR]\b", "rm -fr: recursive force deletion", 0),
    # Block SQL when the statement appears as a command (not inside quotes as a string arg)
    (r"^(?!\s*(?:grep|echo|cat|awk|sed|find|printf)\b)\s*DROP\s+TABLE\b",
     "DROP TABLE: destructive database operation", re.IGNORECASE | re.MULTILINE),
    (r"^(?!\s*(?:grep|echo|cat|awk|sed|find|printf)\b)\s*TRUNCATE\b",
     "TRUNCATE: destructive database operation", re.IGNORECASE | re.MULTILINE),
    (r"^(?!\s*(?:grep|echo|cat|awk|sed|find|printf)\b)\s*DELETE\s+FROM\s+\w+\s*(?:;|$)",
     "DELETE FROM without WHERE clause", re.IGNORECASE | re.MULTILINE),
    (r"\bgit\s+push\s+(?:\S+\s+)*--force\b", "git push --force: destructive force push", 0),
    (r"\bgit\s+push\s+(?:\S+\s+)*-f\b", "git push -f: destructive force push", 0),
]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  project: {project_path}\n")
        f.write(f"  command: {command}\n\n")


def check_command(command: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason)."""
    for pattern, reason, flags in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, flags):
            return True, reason
    return False, ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = os.environ.get("CLAUDE_PROJECT_PATH", os.getcwd())

    blocked, reason = check_command(command)
    if not blocked:
        sys.exit(0)

    log_blocked(command, reason, project_path)

    print(
        json.dumps({
            "decision": "block",
            "reason": (
                f"[BLOCKED by pre-tool-use hook] {reason}.\n"
                f"Command: {command!r}\n"
                f"This command has been logged to {LOG_FILE}.\n"
                "If this was intentional, ask the user to run it manually in a terminal."
            ),
        })
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
