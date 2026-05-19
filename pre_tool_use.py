#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands.

Place at: ~/.claude/hooks/pre_tool_use.py
Hook format: reads JSON from stdin, returns JSON to stdout.
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.expanduser("~/.claude/hooks")

# Destructive command patterns with descriptions
DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf (recursive force delete)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE (deletes entire table with data)'),
    (r'\bgit\s+push\s+.*--force\b', 'git push --force (overwrites remote history)'),
    (r'\bgit\s+push\s+.*-f\b', 'git push -f (force push)'),
    (r'\bTRUNCATE\b', 'TRUNCATE (deletes all rows, no rollback)'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM without WHERE (deletes all rows)'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE (deletes entire database)'),
    (r'\bchmod\s+-R\s+777\b', 'chmod -R 777 (world-writable permission)'),
    (r'\bdd\s+if=', 'dd command (disk destroyer)'),
    (r':\(\)\s*\{\s*:\|:&\s*\}\s*;:', 'fork bomb detected'),
]


def log_blocked(command: str, project_path: str = ""):
    """Log blocked command to file."""
    os.makedirs(HOOK_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path or os.getcwd(),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_destructive(command: str) -> tuple[bool, str]:
    """Check if a command matches any destructive pattern."""
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not valid JSON, allow by default
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Bash/terminal commands
    if tool_name not in ("Bash", "bash", "terminal"):
        print(json.dumps({"continue": True}))
        return

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"continue": True}))
        return

    is_destructive, description = check_destructive(command)

    if is_destructive:
        project_path = os.getcwd()
        log_blocked(command, project_path)

        print(json.dumps({
            "continue": False,
            "reason": (
                f"🚫 DESTRUCTIVE COMMAND BLOCKED: {description}\n"
                f"   Command: {command}\n"
                f"   This command could cause irreversible data loss.\n"
                f"   If you are absolutely sure, use a safer alternative or manually approve.\n"
                f"   Blocked attempt logged to: {LOG_FILE}"
            )
        }))
        return

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
