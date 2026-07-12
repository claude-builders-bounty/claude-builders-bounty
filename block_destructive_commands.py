#!/usr/bin/env python3

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

def log_blocked_command(command, project_path):
    """Log blocked command to file"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "project_path": project_path or "Unknown"
    }
    
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    with open(log_file, "a") as f:
        f.write(f"{json.dumps(log_entry)}\n")

def main():
    # Read the command from stdin
    input_data = json.load(sys.stdin)
    command = input_data.get("command", "")
    project_path = input_data.get("project_path", "")
    
    # Destructive patterns to block
    destructive_patterns = [
        r"rm\s+-rf",
        r"DROP\s+TABLE",
        r"git\s+push\s+--force",
        r"TRUNCATE",
        r"DELETE\s+FROM(?!(?!.*\bWHERE\b))"  # DELETE FROM without WHERE
    ]
    
    # Check if command matches any destructive pattern
    for pattern in destructive_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked_command(command, project_path)
            print(json.dumps({
                "blocked": True,
                "reason": f"Blocked destructive command: {pattern}",
                "message": "Blocked execution of destructive command for security reasons"
            }))
            return
    
    # Special case for DELETE FROM without WHERE clause
    if "DELETE FROM" in command.upper() and "WHERE" not in command.upper():
        log_blocked_command(command, project_path)
        print(json.dumps({
            "blocked": True,
            "reason": "Blocked DELETE FROM without WHERE clause",
            "message": "Blocked execution of DELETE FROM without WHERE clause for security reasons"
        }))
        return
    
    # Special case for git push --force
    if "git push --force" in command:
        log_blocked_command(command, project_path)
        print(json.dumps({
            "blocked": True,
            "reason": "Blocked 'git push --force' command",
            "message": "Blocked execution of 'git push --force' for security reasons"
        }))
        return
    
    # Special case for TRUNCATE
    if "TRUNCATE" in command.upper():
        log_blocked_command(command, project_path)
        print(json.dumps({
            "blocked": True,
            "reason": "Blocked TRUNCATE command",
            "message": "Blocked execution of TRUNCATE for security reasons"
        }))
        return
    
    # If we get here, the command is allowed
    print(json.dumps({
        "blocked": False
    }))

if __name__ == "__main__":
    main()