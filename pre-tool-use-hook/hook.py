#!/usr/bin/env python3
"""
Claude Code Pre-tool-use Hook: Blocks destructive bash commands.

Install: Save this to ~/.claude/hooks/pre-tool-use.py
Make executable: chmod +x ~/.claude/hooks/pre-tool-use.py
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# Commands that are always blocked
ALWAYS_BLOCK = [
    r'rm\s+-rf',
    r'DROP\s+TABLE',
    r'git\s+push\s+--force',
    r'git\s+push\s+-f',
    r'TRUNCATE\s+TABLE',
    r'DELETE\s+FROM\s+[^\s]+\s*;?\s*$',
]

def log_blocked(timestamp, command, project_path, reason):
    """Log blocked attempt to blocked.log"""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BLOCKED_LOG, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {command}\n")
        f.write(f"  Project: {project_path}\n")
        f.write(f"  Reason: {reason}\n")
        f.write("-" * 60 + "\n")

def get_block_reason(command):
    """Get the reason a command is blocked"""
    reasons = {
        r'rm\s+-rf': "Recursive force delete (rm -rf) is dangerous",
        r'DROP\s+TABLE': "DROP TABLE irreversibly deletes table data",
        r'git\s+push\s+--force': "Force push can overwrite remote history",
        r'git\s+push\s+-f': "Force push can overwrite remote history",
        r'TRUNCATE\s+TABLE': "TRUNCATE deletes all rows without backup",
        r'DELETE\s+FROM\s+[^\s]+\s*;?\s*$': "DELETE without WHERE deletes all data",
    }
    for pattern, reason in reasons.items():
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return "Dangerous command detected"

def main():
    """Main hook entry point"""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        sys.exit(1)

    tool_name = payload.get("tool", {}).get("name", "")
    tool_input = payload.get("tool", {}).get("input", {})

    # Only intercept bash tool calls
    if tool_name != "Bash":
        print(json.dumps({"continue": True}))
        return

    command = tool_input.get("command", "")
    cwd = tool_input.get("cwd", os.getcwd())

    timestamp = datetime.now().isoformat()
    project_path = cwd

    # Check if any dangerous pattern matches
    blocked = False
    for pattern in ALWAYS_BLOCK:
        if re.search(pattern, command, re.IGNORECASE):
            blocked = True
            reason = get_block_reason(command)
            log_blocked(timestamp, command, project_path, reason)

            error_msg = (
                f"HOOK BLOCKED: {reason}\n"
                f"Command: {command}\n"
                f"If you need to run this command, disable the pre-tool-use hook or ask the user to approve it manually."
            )
            print(json.dumps({
                "error": error_msg,
                "blocked": True,
                "reason": reason
            }))
            sys.exit(1)

    # Allow the command
    print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()