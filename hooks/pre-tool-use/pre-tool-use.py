#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.

This hook blocks the following patterns:
- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without a WHERE clause

It logs blocked attempts to ~/.claude/hooks/blocked.log.
"""

import json
import sys
import re
from datetime import datetime
import os

# Patterns to block (case-insensitive)
PATTERNS = [
    r'rm\s+-rf',          # rm -rf
    r'DROP\s+TABLE',      # DROP TABLE
    r'git\s+push\s+--force', # git push --force
    r'TRUNCATE',          # TRUNCATE
    r'DELETE\s+FROM',     # DELETE FROM (we'll check for WHERE separately)
]

# Path to the log file
LOG_FILE = os.path.expanduser('~/.claude/hooks/blocked.log')

def log_blocked_command(command, project_path):
    """Log the blocked command to the log file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | {command} | {project_path}\n"
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        # If we can't log, we still want to block the command, so we don't raise.
        pass

def main():
    # Read the input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse the input, we allow the command to proceed.
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "allow",
            }
        }))
        return

    tool_name = input_data.get('toolName', '')
    tool_input = input_data.get('toolInput', {})

    # We only care about Bash tool
    if tool_name != 'Bash':
        # Allow other tools to proceed
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "allow",
            }
        }))
        return

    command = tool_input.get('command', '')
    project_path = tool_input.get('projectPath', os.getcwd())

    # Check if the command matches any of the patterns (case-insensitive)
    command_lower = command.lower()
    blocked = False
    reason = ""

    # Check each pattern
    for pattern in PATTERNS:
        if re.search(pattern, command_lower, re.IGNORECASE):
            blocked = True
            reason = f"Matched pattern: {pattern}"
            break

    # Special check for DELETE FROM without WHERE
    if not blocked and 'delete from' in command_lower:
        # Find the position of 'delete from'
        pos = command_lower.find('delete from')
        # Look for 'where' after the 'delete from'
        if 'where' not in command_lower[pos:]:
            blocked = True
            reason = "DELETE FROM without WHERE clause"

    if blocked:
        # Log the blocked command
        log_blocked_command(command, project_path)

        # Output to block the command
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "block",
                "permissionDecisionReason": f"Blocked destructive command: {reason}"
            }
        }))
    else:
        # Allow the command to proceed
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "allow",
            }
        }))

if __name__ == '__main__':
    main()