#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Blocks:
- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without WHERE
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path


def log_blocked_command(command: str, project_path: str):
    """Log blocked command to file"""
    log_file = Path.home() / ".claude/hooks/blocked.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] Blocked command: {command} (Project: {project_path})\n"
    
    with open(log_file, "a") as f:
        f.write(log_entry)


def is_destructive_command(command: str) -> bool:
    """Check if command contains destructive patterns"""
    command = command.strip()
    
    # Block rm -rf
    if re.search(r'rm\s+-.*r.*f|rm\s+-.*f.*r', command):
        return True
    
    # Block DROP TABLE
    if re.search(r'DROP\s+TABLE', command, re.IGNORECASE):
        return True
    
    # Block git push --force
    if re.search(r'git\s+push\s+.*--force', command):
        return True
    
    # Block TRUNCATE
    if re.search(r'TRUNCATE', command, re.IGNORECASE):
        return True
    
    # Block DELETE FROM without WHERE
    if re.search(r'DELETE\s+FROM', command, re.IGNORECASE) and not re.search(r'WHERE', command, re.IGNORECASE):
        return True
    
    return False


def main():
    """Main hook function"""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
            
        data = json.loads(input_data)
        
        # Check if this is a bash command
        if data.get("tool") == "bash" and "command" in data:
            command = data["command"]
            project_path = data.get("project_path", "unknown")
            
            if is_destructive_command(command):
                log_blocked_command(command, project_path)
                print("BLOCKED: This command has been blocked for safety reasons.")
                print("Reason: Destructive command detected.")
                sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        # Don't block on error, just exit successfully
        sys.exit(0)


if __name__ == "__main__":
    main()