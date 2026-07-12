#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

This hook intercepts and blocks dangerous bash commands that could cause
irreversible damage to the system or data.
"""

import json
import sys
import os
import re
from datetime import datetime


def log_blocked_command(command, project_path):
    """Log blocked command to file"""
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    log_dir = os.path.dirname(log_file)
    
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log the blocked command
    with open(log_file, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Blocked command: {command} | Project: {project_path}\n")


def is_destructive_command(command):
    """Check if command matches destructive patterns"""
    destructive_patterns = [
        r'rm\s+-rf',
        r'DROP\s+TABLE',
        r'git\s+push\s+--force',
        r'TRUNCATE',
        r'DELETE\s+FROM\s+\w+\s*(?!WHERE)',
    ]
    
    for pattern in destructive_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def main():
    # Read the JSON input from stdin
    input_json = sys.stdin.read()
    if not input_json:
        sys.exit(0)  # No input, allow normal execution
    
    try:
        data = json.loads(input_json)
    except json.JSONDecodeError:
        # If JSON is invalid, allow the command to proceed
        sys.exit(0)
    
    # Extract command and project path
    command = data.get('command', '')
    project_path = data.get('project_path', 'Unknown')
    
    # Check if the command is destructive
    if is_destructive_command(command):
        # Log the attempt
        log_blocked_command(command, project_path)
        
        # Print explanation message to Claude
        print("❌ Command blocked by security hook: Destructive bash command detected", file=sys.stderr)
        print(f"   Blocked command: {command}", file=sys.stderr)
        print("   Reason: This command is considered destructive and has been blocked for security.", file=sys.stderr)
        sys.exit(1)  # Block the command
    
    # If not destructive, allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()