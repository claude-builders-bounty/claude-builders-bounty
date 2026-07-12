#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.
"""

import sys
import os
import re
import json
from datetime import datetime
import subprocess

# Patterns to block
BLOCKED_PATTERNS = [
    r'rm -rf',
    r'DROP\s+TABLE',
    r'git push --force',
    r'TRUNCATE',
    r'DELETE\s+FROM(?!\s+\w+\s+WHERE)'
]

def block_command(command):
    """Check if command matches any blocked pattern"""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def log_blocked_command(command):
    """Log blocked command to file"""
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_path = os.getcwd()
        f.write(f"[{timestamp}] Blocked command: {command} in {project_path}\n")

def main():
    # Read the tool use request from stdin
    request = json.loads(sys.stdin.read())
    
    # Check if it's a bash command
    if request.get("tool") != "bash":
        # Not a bash tool use, let it pass through
        json.dump(request, sys.stdout)
        return
        
    command = request.get("input", {}).get("command", "")
    
    # Check if command is blocked
    if block_command(command):
        # Log the blocked attempt
        log_blocked_command(command)
        
        # Output error to Claude
        error_response = {
            "output": f"Error: Command '{command}' is blocked for security reasons.",
            "error": True
        }
        print(json.dumps(error_response))
        return
    
    # If not blocked, allow the command to proceed
    # We still output to Claude that it's blocked but with no error
    if block_command(command):
        error_response = {
            "output": f"Error: Command '{command}' is blocked for security reasons.",
            "error": True
        }
        print(json.dumps(error_response))
        return
    
    # If allowed, pass through the original request
    print(json.dumps(request))

if __name__ == "__main__":
    main()
