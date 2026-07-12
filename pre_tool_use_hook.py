#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.
Install in ~/.claude/hooks/pre_tool_use
"""

import sys
import os
import re
import datetime
from pathlib import Path

def log_blocked_command(command: str, project_path: str):
    """Log blocked command attempts to file"""
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().isoformat()
    with open(log_file, "a") as f:
        f.write(f"{timestamp} | {command} | {project_path}\n")

def is_dangerous_command(command: str) -> bool:
    """Check if command matches any destructive patterns"""
    dangerous_patterns = [
        r"rm\s+-*rf\s*/",  # rm -rf /
        r"rm\s+-*rf\w*\s+.*\/",  # rm -rf with directory path
        r"DROP\s+TABLE",  # SQL drop table
        r"TRUNCATE",  # SQL truncate
        r"DELETE\s+FROM(?!\s+\w+\s+WHERE).",  # SQL delete without where clause
        r"git\s+push\s+--force"  # git force push
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def main():
    # Read the command from stdin
    command = sys.stdin.read().strip()
    
    # Get project path from environment or default to current directory
    project_path = os.environ.get("CLAUDE_PROJECT_PATH", os.getcwd())
    
    # Check if command is dangerous
    if is_dangerous_command(command):
        # Log the blocked command
        log_blocked_command(command, project_path)
        
        # Print explanation for Claude
        print("❌ BLOCKED: This command has been blocked for safety reasons.", file=sys.stderr)
        print("Destructive commands like 'rm -rf', 'DROP TABLE', 'TRUNCATE', 'DELETE FROM' without WHERE, and 'git push --force' are not allowed.", file=sys.stderr)
        print("Check ~/.claude/hooks/blocked.log for details.", file=sys.stderr)
        sys.exit(1)
    
    # If not dangerous, allow command to proceed
    if command:
        print(command)

if __name__ == "__main__":
    main()