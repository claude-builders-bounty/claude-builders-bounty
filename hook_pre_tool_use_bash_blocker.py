#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM (without WHERE)
"""

import sys
import os
import json
import re
from datetime import datetime

# Read the tool use request from stdin
tool_use_request = json.loads(sys.stdin.read())

# Extract command and project path
command = tool_use_request.get("command", "")
project_path = tool_use_request.get("project_path", "unknown")

# List of dangerous patterns to block
dangerous_patterns = [
    r"rm\s+-*rf",
    r"DROP\s+TABLE",
    r"git\s+push\s+.*--force",
    r"TRUNCATE",
    r"DELETE\s+FROM(?!\s+\w+\s+WHERE).*(?=;|$)"
]

# Check if command matches any dangerous pattern
for pattern in dangerous_patterns:
    if re.search(pattern, command, re.IGNORECASE):
        # Log the blocked attempt
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "attempted_command": command,
            "project_path": project_path
        }
        
        log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Output blocking message to Claude
        print(json.dumps({
            "blocked": True,
            "reason": f"Blocked dangerous command: {command}",
            "suggestion": "This command was blocked for security reasons."
        }))
        sys.exit(0)

# If not blocked, allow the command
print(json.dumps({"blocked": False}))
sys.exit(0)