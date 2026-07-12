#!/usr/bin/env python3

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

def log_blocked_command(command: str, project_path: str):
    """Log blocked commands to a file with timestamp, command, and project path."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "project_path": project_path
    }
    
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] Blocked command: {command} in project: {project_path}\n")

def is_destructive_command(command: str) -> bool:
    """Check if a command matches destructive patterns."""
    destructive_patterns = [
        r"rm\s+-rf",
        r"DROP\s+TABLE",
        r"git\s+push\s+--force",
        r"TRUNCATE",
        r"DELETE\s+FROM\s+\w+\s*;",
        r"DELETE\s+FROM\s+\w+\s*WHERE\s+1=1",
        r"DELETE\s+FROM\s+\w+\s*WHERE\s+true",
        r"DELETE\s+FROM\s+\w+\s*$"
    ]
    
    for pattern in destructive_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def main():
    # Read the tool use request from stdin
    request = json.load(sys.stdin)
    
    # Extract command and project path from the request
    command = request.get("command", "")
    project_path = request.get("project_path", "Unknown")
    
    # Check if command is destructive
    if is_destructive_command(command):
        # Log the blocked command
        log_blocked_command(command, project_path)
        
        # Output blocking response to stdout
        response = {
            "block": True,
            "reason": f"Blocked destructive command: {command}",
            "message": f"Blocked potentially destructive command: {command}. This command contains destructive patterns and has been prevented from executing for your safety."
        }
        print(json.dumps(response))
        return
    
    # If not destructive, allow the command
    print(json.dumps({"block": False}))
    
if __name__ == "__main__":
    main()