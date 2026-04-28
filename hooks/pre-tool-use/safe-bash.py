#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"DROP\s+TABLE",
    r"git\s+push\s+--force",
    r"TRUNCATE\s+",
    r"DELETE\s+FROM\s+(?!.*\bWHERE\b)" # DELETE FROM without WHERE
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_path = os.getcwd()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] Command: {command} | Path: {project_path}\n")

def check_command(command):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern
    return False, None

def main():
    # Claude Code hooks receive the tool input as a JSON string
    # or sometimes as raw arguments depending on the hook type.
    # For bash tool, it's typically the command string.
    
    if len(sys.argv) < 2:
        sys.exit(0)
        
    command = " ".join(sys.argv[1:])
    
    is_dangerous, pattern = check_command(command)
    
    if is_dangerous:
        log_blocked(command)
        print(f"\n❌ [SECURITY BLOCK] The command '{command}' matches a dangerous pattern: '{pattern}'.")
        print("This action is prohibited by the pre-tool-use security hook.")
        sys.exit(1) # Non-zero exit code stops execution
        
    sys.exit(0)

if __name__ == "__main__":
    main()
