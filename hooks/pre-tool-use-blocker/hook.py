#!/usr/bin/env python3

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Patterns to block
DANGEROUS_PATTERNS = [
    r'rm\s+-rf',
    r'DROP\s+TABLE',
    r'git\s+push\s+--force',
    r'TRUNCATE\s+(?!TABLE).*;',
    r'DELETE\s+FROM\s+\w+\s*;',
    r'DELETE\s+FROM\s+\w+\s*$', 
]

def is_dangerous_command(command):
    """Check if command matches any dangerous patterns"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def log_blocked_command(command, project_path):
    """Log blocked command to file"""
    log_file = Path.home() / '.claude' / 'hooks' / 'blocked.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Command: {command} | Project: {project_path}\n"
    
    with open(log_file, 'a') as f:
        f.write(log_entry)

def main():
    # Read input from stdin (Claude Code hook format)
    input_data = sys.stdin.read()
    if not input_data:
        return 0  # No input, allow by default
        
    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        # If not JSON, treat as plain text command
        command = input_data.strip()
        data = {"command": command, "project_path": os.getcwd()}
    
    command = data.get('command', '')
    project_path = data.get('project_path', os.getcwd())
    
    if is_dangerous_command(command):
        log_blocked_command(command, project_path)
        print(f"❌ BLOCKED: Dangerous command detected\n\nCommand: {command}\nReason: Matches destructive pattern\n\nThis command was blocked for your safety. Check ~/.claude/hooks/blocked.log for details.")
        return 1  # Non-zero exit code blocks execution
    
    return 0  # Allow command to proceed

if __name__ == "__main__":
    sys.exit(main())