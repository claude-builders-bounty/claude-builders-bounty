#!/usr/bin/env python3
"""
pre-tool-use hook: Blocks dangerous bash commands before Claude Code executes them.
Logs blocked attempts. Displays clear explanation to Claude.

Install: See README.md
"""

import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', "Recursive force delete (rm -rf) is blocked to prevent accidental data loss."),
    (r'\brm\s+.*-r.*-f\b', "Recursive force delete (rm -rf variant) is blocked."),
    (r'\bDROP\s+TABLE\b', "DROP TABLE is blocked to prevent database destruction."),
    (r'\bTRUNCATE\b', "TRUNCATE is blocked to prevent mass data deletion."),
    (r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)', "DELETE FROM without a WHERE clause is blocked — would delete all rows."),
    (r'\bgit\s+push\s+.*--force\b', "Force push (git push --force) is blocked to prevent history rewriting."),
    (r'\bgit\s+push\s+.*-f\b', "Force push (git push -f) is blocked to prevent history rewriting."),
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append blocked attempt to log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] BLOCKED | project={project_path} | reason={reason} | command={command}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Returns (is_blocked, reason).
    Checks against all BLOCKED_PATTERNS (case-insensitive).
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON — let it through
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Bash tool calls
    if tool_name not in ("Bash", "bash"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = hook_input.get("cwd", os.getcwd())

    blocked, reason = check_command(command)
    if not blocked:
        sys.exit(0)

    # Log the blocked attempt
    log_blocked(command, reason, project_path)

    # Output Claude-readable block message via stderr (shown to Claude)
    block_message = {
        "type": "error",
        "message": (
            f"🚫 BLOCKED: {reason}\n"
            f"Command: {command}\n"
            f"Logged to: {LOG_FILE}\n"
            "To proceed, reformulate the command safely (e.g., add a WHERE clause, "
            "use 'rm' without -rf, or use 'git push' without --force)."
        )
    }
    print(json.dumps(block_message), file=sys.stderr)

    # Exit code 2 = block the tool call and show message to Claude
    sys.exit(2)


if __name__ == "__main__":
    main()
