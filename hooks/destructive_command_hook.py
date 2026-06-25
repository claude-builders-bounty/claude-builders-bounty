#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook
Blocks dangerous bash commands before execution.
"""
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that indicate destructive commands
DESTRUCTIVE_PATTERNS = [
    # File system destruction
    (r"rm\s+(-[^\s]*)?\s*-rf\s+", "Recursive force delete"),
    (r"rm\s+(-[^\s]*)?\s*-fr\s+", "Recursive force delete"),
    (r"rm\s+(-[^\s]*)?\s*/\s*", "Delete from root"),
    
    # Database destruction
    (r"DROP\s+TABLE\s+", "Drop database table"),
    (r"TRUNCATE\s+", "Truncate table/data"),
    (r"DELETE\s+FROM\s+(?!.*WHERE)", "DELETE without WHERE clause"),
    
    # Git destruction
    (r"git\s+push\s+.*--force(?!-with-lease)", "Force push to remote"),
    (r"git\s+push\s+.*\s+-f\s", "Force push to remote"),
    
    # Disk/partition destruction
    (r"mkfs\.", "Format filesystem"),
    (r"dd\s+.*of=/dev/", "Write to device"),
    (r"fdisk\s+", "Disk partitioning"),
]

def log_blocked_attempt(command: str, project_path: str, reason: str):
    """Log blocked command to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches destructive patterns."""
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    """Main hook entry point."""
    # Read hook input from stdin (Claude Code format)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If not JSON, check the raw command
        input_data = {"command": sys.stdin.read().strip()}
    
    command = input_data.get("command", "")
    project_path = input_data.get("project_path", os.getcwd())
    
    is_destructive, reason = check_command(command)
    
    if is_destructive:
        log_blocked_attempt(command, project_path, reason)
        
        # Return block decision to Claude Code
        response = {
            "decision": "block",
            "reason": f"\n\n🚫 BLOCKED: {reason}\n\n"
                     f"The command was blocked because it matches a destructive pattern.\n"
                     f"Command: {command}\n\n"
                     f"If you need to run this command, please ask the user to run it manually\n"
                     f"or modify the command to be less destructive.\n\n"
                     f"Example alternatives:\n"
                     f"- Use 'rm -i' for interactive deletion\n"
                     f"- Use 'git push --force-with-lease' instead of --force\n"
                     f"- Add a WHERE clause to DELETE statements\n"
        }
    else:
        response = {"decision": "allow"}
    
    print(json.dumps(response))
    return 0 if not is_destructive else 1

if __name__ == "__main__":
    sys.exit(main())
