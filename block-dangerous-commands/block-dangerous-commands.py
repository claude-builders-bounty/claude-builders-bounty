#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Installation:
    mkdir -p ~/.claude/hooks
    cp block-dangerous-commands.py ~/.claude/hooks/
    chmod +x ~/.claude/hooks/block-dangerous-commands.py

Usage:
    This hook is automatically invoked by Claude Code before bash commands.
"""

import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path

# Patterns that should be blocked
BLOCKED_PATTERNS = [
    # File system destruction
    (r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)*-[a-zA-Z]*r[a-zA-Z]*\s', 'Recursive force delete'),
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)*-[a-zA-Z]*f[a-zA-Z]*\s', 'Recursive force delete'),
    (r'\brm\s+-rf\s', 'Recursive force delete'),
    (r'\brm\s+-fr\s', 'Recursive force delete'),
    (r'\brm\s+--recursive\s+--force\b', 'Recursive force delete'),
    (r'\brmdir\s+/[/*]\s', 'Deleting root directory'),
    
    # Database destruction
    (r'\bDROP\s+TABLE\b', 'DROP TABLE without safety check'),
    (r'\bTRUNCATE\s+TABLE?\b', 'TRUNCATE without safety check'),
    (r'\bDELETE\s+FROM\b(?![\s\S]*WHERE)', 'DELETE without WHERE clause'),
    (r'\bDELETE\s+\*\s+FROM\b', 'DELETE all rows'),
    
    # Git destructive operations
    (r'\bgit\s+push\s+.*--force\b', 'Force push to remote'),
    (r'\bgit\s+push\s+.*-[a-zA-Z]*f[a-zA-Z]*\b', 'Force push to remote'),
    (r'\bgit\s+push\s+.*--delete\b', 'Delete remote branch'),
    (r'\bgit\s+reset\s+--hard\b', 'Hard reset (loses changes)'),
    (r'\bgit\s+clean\s+-[a-zA-Z]*f[a-zA-Z]*\b', 'Force clean untracked files'),
    (r'\bgit\s+checkout\s+.*--force\b', 'Force checkout (loses changes)'),
    
    # System destruction
    (r'\bmkfs\b', 'Format filesystem'),
    (r'\bdd\s+if=', 'Disk write operation'),
    (r'\bformat\s+[a-zA-Z]:', 'Format disk drive'),
    
    # Permission/ownership changes on system directories
    (r'\bchmod\s+[0-7]*\s+/(usr|etc|var|bin|sbin|lib)\b', 'Changing system directory permissions'),
    (r'\bchown\s+.*:.*\s+/(usr|etc|var|bin|sbin|lib)\b', 'Changing system directory ownership'),
]

def get_log_path():
    """Get the path to the blocked commands log file."""
    claude_dir = Path.home() / ".claude" / "hooks"
    claude_dir.mkdir(parents=True, exist_ok=True)
    return claude_dir / "blocked.log"

def log_blocked_command(command, pattern_match, project_path):
    """Log a blocked command to the log file."""
    log_path = get_log_path()
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "pattern": pattern_match,
        "project": project_path,
        "user": os.getenv("USER", "unknown")
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def is_command_blocked(command):
    """Check if a command matches any blocked patterns."""
    command_upper = command.upper()
    
    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    
    return False, None

def main():
    """Main hook function."""
    try:
        # Read the input from Claude Code
        input_data = json.load(sys.stdin)
        
        # Extract the command
        command = input_data.get("command", "")
        project_path = input_data.get("project_path", os.getcwd())
        
        # Check if command is blocked
        is_blocked, pattern_match = is_command_blocked(command)
        
        if is_blocked:
            # Log the blocked command
            log_blocked_command(command, pattern_match, project_path)
            
            # Return a rejection message
            response = {
                "decision": "block",
                "reason": f"🚫 Command blocked: {pattern_match}\n\n"
                          f"This command was blocked by the safety hook because it could cause "
                          f"irreversible damage. If you believe this is a false positive, please "
                          f"modify the command to be less destructive or run it manually."
            }
        else:
            # Allow the command
            response = {"decision": "allow"}
        
        # Output the response
        json.dump(response, sys.stdout)
        sys.exit(0)
        
    except Exception as e:
        # On error, allow the command but log the error
        json.dump({"decision": "allow"}, sys.stdout)
        sys.exit(0)

if __name__ == "__main__":
    main()
