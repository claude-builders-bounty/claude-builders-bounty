#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

Installation:
1. Copy this file to ~/.claude/hooks/block-destructive.py
2. Make it executable: chmod +x ~/.claude/hooks/block-destructive.py
3. Add to ~/.claude/settings.json:
   {
     "hooks": {
       "pre-tool-use": [
         {
           "matcher": "bash",
           "hook": "~/.claude/hooks/block-destructive.py"
         }
       ]
     }
   }
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf variants
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|(-[a-zA-Z]*f[a-zA-Z]*r))\b', 'rm -rf (recursive force delete)'),
    (r'\brm\s+-rf\b', 'rm -rf (recursive force delete)'),
    (r'\brm\s+-fr\b', 'rm -fr (force recursive delete)'),
    
    # SQL destructive commands
    (r'\bDROP\s+(TABLE|DATABASE)\b', 'DROP TABLE/DATABASE (data destruction)'),
    (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE (data destruction)'),
    (r'\bDELETE\s+FROM\s+\w+\s*;', 'DELETE without WHERE clause (mass deletion)'),
    (r'\bDELETE\s+FROM\s+\w+\s*$', 'DELETE without WHERE clause (mass deletion)'),
    
    # Git dangerous operations
    (r'\bgit\s+push\s+.*--force\b', 'git push --force (rewrites history)'),
    (r'\bgit\s+push\s+-f\b', 'git push -f (rewrites history)'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard (loses uncommitted changes)'),
    
    # System-level destructive
    (r'\bdd\s+.*\bof=/dev/', 'dd to device (can overwrite disk)'),
    (r'\bmkfs\b', 'mkfs (formats filesystem)'),
    (r'\bformat\s+[a-zA-Z]:', 'format drive (Windows)'),
]

LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def log_blocked(command: str, project_path: str, pattern_name: str):
    """Log blocked command attempt."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {pattern_name}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += f"  {'='*60}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if command matches dangerous patterns.
    Returns (is_dangerous, pattern_name).
    """
    # Normalize whitespace
    normalized = ' '.join(command.split())
    
    for pattern, name in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, name
    
    return False, ""

def main():
    """Main hook entry point."""
    # Read input from stdin (Claude Code passes tool input as JSON)
    try:
        input_data = json.load(sys.stdin)
        command = input_data.get('command', '')
        project_path = input_data.get('cwd', os.getcwd())
    except (json.JSONDecodeError, KeyError):
        # If we can't parse input, allow the command
        sys.exit(0)
    
    # Check if command is dangerous
    is_dangerous, pattern_name = check_command(command)
    
    if is_dangerous:
        # Log the blocked attempt
        log_blocked(command, project_path, pattern_name)
        
        # Output block message to stderr (Claude Code will show this)
        error_msg = f"""
⚠️  BLOCKED: Destructive command detected

Pattern: {pattern_name}
Command: {command}

This command has been blocked to prevent accidental data loss.
If you really need to run this, use: bypass-destructive <command>

Logged to: {LOG_FILE}
"""
        print(error_msg, file=sys.stderr)
        
        # Exit with non-zero to block the command
        sys.exit(1)
    
    # Command is safe, allow it
    sys.exit(0)

if __name__ == '__main__':
    main()
