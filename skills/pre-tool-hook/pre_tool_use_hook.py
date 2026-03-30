#!/usr/bin/env python3
"""
Pre-tool-use hook to block destructive bash commands.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

# Log file location
LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_block(command: str, reason: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        timestamp = datetime.now(timezone.utc).isoformat()
        f.write(f"[{timestamp}] command={command} reason={reason}\n")

def is_destructive(command: str) -> tuple[bool, str]:
    """Check if command matches dangerous patterns."""
    cmd_lower = command.lower().strip()

    # 1. rm -rf (any path)
    if re.search(r'rm\s+-rf\b', cmd_lower):
        return True, "Blocked: 'rm -rf' is too destructive"

    # 2. DROP TABLE (SQL)
    if re.search(r'drop\s+table\b', cmd_lower):
        return True, "Blocked: 'DROP TABLE' without explicit approval"

    # 3. git push --force
    if re.search(r'git\s+push\s+--force\b', cmd_lower):
        return True, "Blocked: 'git push --force' can rewrite history"

    # 4. TRUNCATE
    if re.search(r'truncate\s+table\b', cmd_lower):
        return True, "Blocked: 'TRUNCATE' without explicit approval"

    # 5. DELETE FROM without WHERE (heuristic)
    if re.search(r'delete\s+from\b', cmd_lower):
        # Check if there's a WHERE clause
        if not re.search(r'where\b', cmd_lower):
            return True, "Blocked: 'DELETE FROM' without WHERE clause"
    return False, ""

def main():
    try:
        # Read JSON payload from stdin
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Invalid JSON payload", file=sys.stderr)
        sys.exit(1)

    tool = payload.get("tool", "")
    input_data = payload.get("input", {})
    command = input_data.get("command", "")

    if tool == "bash" and command:
        blocked, reason = is_destructive(command)
        if blocked:
            log_block(command, reason)
            print(reason, file=sys.stderr)
            sys.exit(1)

    # Allow all other commands
    sys.exit(0)

if __name__ == "__main__":
    main()
