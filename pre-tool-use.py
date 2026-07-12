#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.

This hook blocks dangerous commands like:
- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without WHERE clause
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

def log_blocked_command(command, project_path):
    """Log blocked command to file"""
    log_file = Path.home() / '.claude' / 'hooks' / 'blocked.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": str(project_path)
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def is_destructive_command(command):
    """Check if command is destructive"""
    # Normalize command for checking
    cmd = command.strip().lower()
    
    # Check for rm -rf
    if re.search(r'rm\s+-.*rf?.*\/', cmd) or re.search(r'rm\s+-.*f.*r.*\/', cmd):
        return True, "rm -rf command blocked"
    
    # Check for DROP TABLE
    if 'drop table' in cmd:
        return True, "DROP TABLE command blocked"
    
    # Check for git push --force
    if 'git push' in cmd and ('--force' in cmd or '-f' in cmd):
        return True, "git push --force command blocked"
    
    # Check for TRUNCATE
    if cmd.strip().startswith('truncate'):
        return True, "TRUNCATE command blocked"
    
    # Check for DELETE FROM without WHERE
    if re.search(r'delete\s+from\s+\w+', cmd, re.IGNORECASE) and 'where' not in cmd:
        return True, "DELETE FROM without WHERE clause blocked"
    
    return False, ""

def main():
    """Main hook function"""
    if len(sys.argv) < 2:
        # No command provided, allow execution
        sys.exit(0)
    
    command = sys.argv[1]
    project_path = Path.cwd()
    
    is_destructive, reason = is_destructive_command(command)
    
    if is_destructive:
        log_blocked_command(command, project_path)
        print(f"❌ BLOCKED: {reason}")
        print(f"Command: {command}")
        sys.exit(1)
    
    # Command is safe, allow execution
    sys.exit(0)

if __name__ == "__main__":
    main()