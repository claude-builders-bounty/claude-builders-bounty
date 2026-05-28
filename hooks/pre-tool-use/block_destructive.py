#!/usr/bin/env python3
"""
Pre-tool-use hook: block destructive bash commands.
Install: cp -r hooks/pre-tool-use ~/.claude/hooks/

Usage from Claude Code hooks config:
  name: block-destructive
  hook: /path/to/block_destructive.py
"""
import sys
import re
import os
from datetime import datetime

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns to block
PATTERNS = [
    r"rm\s+-rf",                  # Recursive forced removal
    r"DROP\s+TABLE",               # Database drop table
    r"git\s+push\s+--force",       # Force push
    r"TRUNCATE",                   # Database truncate
    r"DELETE\s+FROM\s+WHERE",      # DELETE without WHERE (use parameterized queries)
]

def is_blocked(command: str) -> bool:
    """Check if command matches any blocked pattern."""
    for pattern in PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def log_blocked(command: str, project_path: str) -> None:
    """Log blocked attempt to blocked.log."""
    os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(BLOCKED_LOG, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {command} | Project: {project_path}\n")

def main():
    if len(sys.argv) < 2:
        sys.exit(0)  # No command provided, allow

    command = sys.argv[1]
    project_path = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()

    if is_blocked(command):
        log_blocked(command, project_path)
        print("Hook: Destructive command blocked.")
        print("This command was blocked by the pre-tool-use hook because it matches a dangerous pattern.")
        print("If you need to proceed, please review the command and run it manually with caution.")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
