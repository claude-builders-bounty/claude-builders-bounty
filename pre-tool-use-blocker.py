#!/usr/bin/env python3

import os
import sys
import time
from pathlib import Path

def log_blocked_command(command, project_path):
    log_file = Path.home() / ".cla0de" / "hooks" / "blocked.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Blocked command: {command} in {project_path}\n")

def is_dangerous_command(command):
    dangerous_patterns = [
        "rm -rf",
        "DROP TABLE",
        "TRUNCATE",
        "git push --force"
    ]
    
    # Check for DELETE FROM without WHERE clause
    if "DELETE FROM" in command and "WHERE" not in command:
        return True
        
    for pattern in dangerous_patterns:
        if pattern in command:
            return True
    return False

def main():
    if len(sys.argv) < 2:
        return 0
        
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    project_path = os.getcwd()
    
    if is_dangerous_command(command):
        print("Blocked potentially destructive command:", command)
        log_blocked_command(command, project_path)
        return 1
        
    return 0

    # Log every blocked attempt
    log_blocked_command(command, project_path)
    
    # Block if dangerous
    if is_dangerous_command(command):
        print(f"Blocked potentially destructive command: {command}")
        return 1
        
    return 0

if __name__ == "__main__":
    if not os.environ.get("CLAUDE_HOOK_TYPE"):
        sys.exit(main())
    else:
        sys.exit(0)