#!/usr/bin/env python3
"""
PreToolUse hook that blocks destructive bash commands.
Place at ~/.claude/hooks/block-destructive.py

Exit codes:
  0 - Allow tool to proceed
  1 - Error (shown to user, not Claude)
  2 - Block tool call and show message to Claude
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

BLOCKED_PATTERNS = [
    # rm -rf (any variant)
    (r"\brm\s+-rf\b", "rm -rf (recursive force remove)"),
    # DROP TABLE
    (r"\bDROP\s+TABLE\b", "DROP TABLE (database table deletion)"),
    # git push --force (including --force-with-lease)
    (r"\bgit\s+push\s+.*--force", "git push --force (force push to remote)"),
    # TRUNCATE
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE (table data removal)"),
    # DELETE FROM without WHERE clause
    (r"\bDELETE\s+FROM\s+\w+\s*(;|$)", "DELETE FROM without WHERE clause"),
    # rm -r (recursive without -f, still dangerous)
    (r"\brm\s+.*-r\b", "rm -r (recursive remove)"),
    # git reset --hard
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard (destructive git reset)"),
    # chmod -R 777
    (r"\bchmod\s+.*-R\s+777\b", "chmod -R 777 (world-writable permissions)"),
    # fork bomb
    (r":\(\)\s*\{", "fork bomb pattern detected"),
    # dd targeting disk devices
    (r"\bdd\s+if=.*of=/dev/\w+", "dd to disk device"),
    # > /dev/sda or similar
    (r">\s*/dev/sd[a-z]", "redirect to raw disk device"),
    # mv to /dev/null
    (r"\bmv\s+.*/dev/null\b", "mv to /dev/null"),
    # format / mkfs
    (r"\bmkfs\.\w+", "mkfs (filesystem format)"),
]


def log_blocked(command: str, cwd: str, pattern_name: str) -> None:
    """Log a blocked command attempt."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": cwd,
        "blocked_by": pattern_name,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"block-destructive: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    cwd = input_data.get("cwd", os.getcwd())

    for pattern, pattern_name in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, cwd, pattern_name)

            message = (
                f"BLOCKED: Destructive command detected - {pattern_name}\n"
                f"  Command: {command}\n"
                f"  Reason: This command could cause irreversible data loss.\n"
                f"  Logged to: {LOG_FILE}\n"
                f"  To proceed, use a safer alternative or review the operation manually."
            )
            # Write to stdout as JSON for Claude
            output = {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                },
                "systemMessage": message,
            }
            print(json.dumps(output))
            sys.exit(2)

    # All checks passed
    sys.exit(0)


if __name__ == "__main__":
    main()
