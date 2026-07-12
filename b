#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.

Place this file at: ~/.claude/hooks/block-destructive-commands.py
And make it executable: chmod +x ~/.claude/hooks/block-destructive-commands.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# Path to the log file
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Destructive patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf variations
    {
        "pattern": r"rm\s+(-先后|先后|)\s*-\S*r\S*f",
        "description": "rm -rf: recursively and forcefully removes files/directories",
    },
    {
        "pattern": r"rm\s+.*-.*[rf].*-.*[rf]",
        "description": "rm with recursive and force flags",
    },
    # DROP TABLE
    {
        "pattern": r"(?i)\bDROP\s+TABLE\b",
        "description": "DROP TABLE: deletes an entire database table",
    },
    # git push --force
    {
        "pattern": r"(?i)git\s+push\s+.*--force",
        "description": "git push --force: overwrites remote history, can delete others' work",
    },
    {
        "pattern": r"(?i)git\s+push\s+.*-f\b",
        "description": "git push -f: overwrites remote history, can delete others' work",
    },
    # TRUNCATE
    {
        "pattern": r"(?i)\bTRUNCATE\b",
        "description": "TRUNCATE: removes all rows from a table without logging individual rows",
    },
    # DELETE FROM without WHERE
    {
        "pattern": r"(?i)\bDELETE\s+FROM\s+\S+(?!.*\bWHERE\b).*",
        "description": "DELETE FROM without WHERE: deletes all rows from a table",
    },
]


def log_blocked_attempt(command: str, project_path: str):
    """Log a blocked command attempt to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path,
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any dangerous pattern. Returns (is_blocked, reason)."""
    for rule in DANGEROUS_PATTERNS:
        if re.search(rule["pattern"], command):
            return True, rule["description"]
    return False, ""


def main():
    # Read the hook input from stdin (Claude Code passes tool use info as JSON)
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not a valid JSON input, allow to proceed
        sys.exit(0)
    
    # Extract tool information
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    
    # Only check bash tool
    if tool_name != "bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    project_path = hook_input.get("project_path", os.getcwd())
    
    is_blocked, reason = check_command(command)
    
    if is_blocked:
        log_blocked_attempt(command, project_path)
        
        # Output the blocking message to stderr so Claude sees it
        print(f"\n🛡️  BLOCKED: This command was prevented from running.\n   Reason: {reason}\n   Command: {command}\n", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

--- /dev/null
# Block Destructive Commands Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they are executed.

## Installation

