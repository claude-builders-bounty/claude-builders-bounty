#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.

Installation:
1. Make executable: chmod +x pre_tool_use_hook.py
2. Move to ~/.claude/hooks/
"""

import os
import sys
import re
from datetime import datetime
import subprocess

# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    r'rm\s+-rf',
    r'rm\s+-fr',
    r'DROP\s+TABLE',
    r'TRUNCATE\s+(?!TABLE).*',
    r'DELETE\s+FROM(?:(?!\bWHERE\b).)*$',
    r'git\s+push\s+--force'
]

def log_blocked_command(command, project_path):
    """Log blocked command to the log file"""
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Command: {command.strip()}; Project: {project_path}\n")

def main():
    # Read the command from stdin
    command = sys.stdin.read().strip()
    
    # Get the project path from environment variable or current directory
    project_path = os.environ.get("PROJECT_PATH", os.getcwd())
    
    # Check if command matches any dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Log the blocked command
            log_blocked_command(command, project_path)
            
            # Explain why the command was blocked
            print("❌ BLOCKED DESTRUCTIVE COMMAND", file=sys.stderr)
            print(f"Command blocked: {command}", file=sys.stderr)
            print("Reason: This command contains potentially destructive patterns", file=sys.stderr)
            print("Blocked patterns: rm -rf, DROP TABLE, TRUNCATE, DELETE FROM (without WHERE), git push --force", file=sys.stderr)
            sys.exit(1)
    
    # If we get here, the command is safe to execute
    sys.exit(0)

if __name__ == "__main__":
    main()