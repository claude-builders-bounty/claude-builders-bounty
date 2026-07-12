#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.
"""

import sys
import os
import json
import datetime

def log_blocked_command(command, project_path):
    """Log blocked commands to file"""
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Blocked command: {command} | Project: {project_path}\n")

def is_destructive_command(command):
    """Check if command contains destructive patterns"""
    destructive_patterns = [
        "rm -rf",
        "DROP TABLE",
        "git push --force",
        "TRUNCATE",
        "DELETE FROM"
    ]
    
    # Check for DELETE FROM without WHERE clause
    if command.strip().upper().startswith("DELETE FROM") and "WHERE" not in command.upper():
        return True
        
    # Check for other destructive patterns
    return any(pattern in command for pattern in destructive_patterns)

if __name__ == "__main__":
    pass