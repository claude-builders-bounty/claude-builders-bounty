#!/usr/bin/env python3

import sys
import os
import json
import re
from datetime import datetime

def block_destructive_commands():
    # Read the tool use data from stdin
    data = json.load(sys.stdin)
    
    # Log the attempt
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_path = data.get('cwd', 'Unknown')
    
    log_entry = f"{timestamp} - Blocked command: {data['command']} in project {project_path}\n"
    
    # Append to blocked.log
    with open(os.path.expanduser("~/.claude/hooks/blocked.log"), "a") as log_file:
        log_file.write(log_entry)
    
    # Check if command should be blocked
    dangerous_patterns = [
        r'rm\s+-rf',
        r'DROP\s+TABLE',
        r'git\s+push\s+--force',
        r'TRUNCATE',
        r'DELETE\s+FROM\s+\w+\s*$'
    ]
    
    command = data['command']
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            print(f"❌ Blocked dangerous command: {command}")
            print("This command has been blocked for safety.")
            return True
    
    return False

if __name__ == "__main__":
    if block_destructive_commands():
        sys.exit(1)
    else:
        # If no dangerous commands found, output the original command
        print(json.dumps({
            "command": sys.argv[1] if len(sys.argv) > 1 else "",
            "cwd": os.getcwd()
        }))
        sys.exit(0)

