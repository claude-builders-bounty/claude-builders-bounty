#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

# Setup paths
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")

# Patterns to block
BLOCKED_PATTERNS = [
    r"rm\s+-rf",
    r"(?i)DROP\s+TABLE",
    r"git\s+push\s+--force",
    r"(?i)TRUNCATE",
    r"(?i)DELETE\s+FROM\s+(?!.*WHERE).*"  # DELETE FROM without WHERE
]

def log_blocked(command, cwd):
    os.makedirs(HOOKS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: '{command}' | PATH: {cwd}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def main():
    # Read payload from stdin
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If not JSON, allow to pass or ignore
        sys.exit(0)
        
    tool_name = payload.get("tool", "")
    tool_input = payload.get("input", {})
    
    # We only care about tools that execute commands
    if tool_name not in ["bash", "run_command", "execute"]:
        sys.exit(0)
        
    # Extract the command (Claude Code usually passes it as 'command' or 'CommandLine')
    command = tool_input.get("command") or tool_input.get("CommandLine", "")
    cwd = tool_input.get("Cwd", os.getcwd())
    
    if not command:
        sys.exit(0)
        
    # Check against blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            log_blocked(command, cwd)
            # Output clear message to stderr/stdout for Claude to see
            print(f"SECURITY HOOK ALERT: The command '{command}' contains a forbidden destructive pattern.")
            print("Action Blocked: To protect the system, operations like 'rm -rf', 'DROP TABLE', and 'git push --force' are restricted.")
            # Exit with non-zero status to abort tool execution
            sys.exit(1)
            
    # Allow command
    sys.exit(0)

if __name__ == "__main__":
    main()
