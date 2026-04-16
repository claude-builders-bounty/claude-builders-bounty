#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Guard
Blocks dangerous bash commands and logs attempts.
"""
import sys
import os
import re
import datetime

# Configuration
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",            # Root deletion
    r"rm\s+-rf\s+\*",           # Wildcard deletion
    r"DROP\s+TABLE",            # SQL Drop
    r"DELETE\s+FROM\s+(?!.*WHERE)", # SQL Delete without WHERE
    r"TRUNCATE\s+TABLE",        # SQL Truncate
    r"git\s+push\s+--force",    # Force push
    r"mkfs",                    # Format disk
    r"dd\s+if="                 # Disk write
]

def log_blocked(command):
    timestamp = datetime.datetime.now().isoformat()
    project_path = os.getcwd()
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {command} | PATH: {project_path}\n")

def check_command(command):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern
    return False, None

def main():
    # Claude Code passes the command as a string to the hook
    if len(sys.argv) < 2:
        sys.exit(0)

    command = " ".join(sys.argv[1:])
    is_dangerous, pattern = check_command(command)

    if is_dangerous:
        log_blocked(command)
        print(f"\n❌ [GUARD] COMMAND BLOCKED: Destructive pattern detected ('{pattern}').")
        print(f"Safety First: This command was intercepted to prevent accidental data loss.")
        sys.exit(1) # Non-zero exit blocks execution

    sys.exit(0)

if __name__ == "__main__":
    main()
