#!/usr/bin/env python3
"""
Pre-tool-use Hook: Blocks destructive bash commands
Issue #3 - Claude Builders Bounty

Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
Logs to: ~/.claude/hooks/blocked.log
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    r'\brm\s+(-[rf]+\s+|--recursive\s+|--force\s+)',
    r'\brm\s+-rf\b',
    r'\bgit\s+push\s+.*(--force|-f)\b',
    r'\bDROP\s+TABLE\b',
    r'\bTRUNCATE\s+TABLE\b',
    r'\bTRUNCATE\b',
    r'\bDELETE\s+FROM\b.*(?!\s+WHERE\b)',
]

# Log file path
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

def log_blocked_command(command: str, project_path: str) -> None:
    """Log blocked command to file"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | BLOCKED | {command} | {project_path}\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if command should be blocked
    
    Returns: (blocked, reason)
    """
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Determine reason
            if 'rm' in command.lower():
                return True, "⚠️ BLOCKED: 'rm -rf' detected - prevents accidental file deletion"
            elif 'git push --force' in command.lower() or 'git push -f' in command.lower():
                return True, "⚠️ BLOCKED: 'git push --force' detected - prevents overwriting remote history"
            elif 'DROP TABLE' in command.upper():
                return True, "⚠️ BLOCKED: 'DROP TABLE' detected - prevents database destruction"
            elif 'TRUNCATE' in command.upper():
                return True, "⚠️ BLOCKED: 'TRUNCATE' detected - prevents data loss"
            elif 'DELETE FROM' in command.upper():
                # Check if WHERE clause exists
                if 'WHERE' not in command.upper():
                    return True, "⚠️ BLOCKED: 'DELETE FROM' without WHERE clause detected - prevents accidental mass deletion"
    
    return False, ""

def main():
    """Main hook entry point"""
    # Read input from stdin (Claude Code passes JSON)
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # If not JSON, treat as raw command
        input_data = {"command": sys.stdin.read()}
    
    # Extract command and project path
    command = input_data.get("command", "")
    project_path = input_data.get("project_path", os.getcwd())
    
    # Check command
    blocked, reason = check_command(command)
    
    if blocked:
        # Log the blocked attempt
        log_blocked_command(command, project_path)
        
        # Output rejection message
        output = {
            "decision": "reject",
            "message": f"{reason}\n\nPlease use a safer alternative:\n- For files: use 'rm -i' (interactive) or move to temp first\n- For git: use 'git push --force-with-lease' instead\n- For database: add WHERE clause or use transactions"
        }
        print(json.dumps(output))
        sys.exit(0)
    
    # Allow the command
    output = {
        "decision": "allow"
    }
    print(json.dumps(output))
    sys.exit(0)

if __name__ == "__main__":
    main()