#!/usr/bin/env python3
import sys
import os
import re
import datetime

# Configuration
HOOK_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")

# Patterns to block
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"DROP\s+TABLE",
    r"git\s+push\s+--force",
    r"TRUNCATE\s+",
    r"DELETE\s+FROM\s+(?!.*\bWHERE\b)"
]

def log_blocked(command):
    if not os.path.exists(HOOK_DIR):
        os.makedirs(HOOK_DIR)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_path = os.getcwd()
    
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] COMMAND: {command} | PATH: {project_path}\n")

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
    
    # Claude Code passes the command as the first argument in the pre-tool-use hook
    command = sys.argv[1]
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command)
            print(f"\n❌ [SECURITY BLOCK] The command '{command}' was blocked because it contains a dangerous pattern: {pattern}")
            print("To override this, please perform the action manually if you are absolutely sure.")
            sys.exit(1) # Exit with non-zero to block execution

    sys.exit(0) # Allow execution

if __name__ == "__main__":
    main()
