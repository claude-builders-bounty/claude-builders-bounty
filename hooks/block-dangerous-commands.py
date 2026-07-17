#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook - Block Dangerous Bash Commands

This hook intercepts dangerous bash commands before they are executed
and blocks them with a clear explanation.

Usage:
  Add to ~/.claude/settings.json:
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 ~/.claude/hooks/block-dangerous-commands.py"
            }
          ]
        }
      ]
    }
  }
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

# Patterns to block (case-insensitive)
BLOCKED_PATTERNS = [
    (r'rm\s+-rf\b', 'Recursive force deletion (rm -rf)'),
    (r'DROP\s+TABLE\b', 'Database table deletion (DROP TABLE)'),
    (r'git\s+push\s+--force\b', 'Force push to remote (git push --force)'),
    (r'TRUNCATE\b', 'Table truncation (TRUNCATE)'),
    (r'DELETE\s+FROM\b(?![\s\S]*WHERE)', 'Mass deletion without WHERE clause (DELETE FROM)'),
]

LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def log_blocked_attempt(command: str, reason: str, project_path: str):
    """Log blocked attempt to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += f"  ---\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked patterns."""
    command_lower = command.lower()
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Special case: DELETE FROM with WHERE is allowed
            if 'DELETE FROM' in reason:
                if re.search(r'DELETE\s+FROM\b[\s\S]*WHERE\b', command, re.IGNORECASE):
                    continue
            return True, reason
    
    return False, ""

def main():
    """Main hook function."""
    # Read input from Claude Code (JSON format)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If no JSON input, allow command
        sys.exit(0)
    
    # Extract command from input
    command = input_data.get('command', '')
    project_path = input_data.get('project_path', os.getcwd())
    
    # Check if command is dangerous
    is_blocked, reason = check_command(command)
    
    if is_blocked:
        # Log the blocked attempt
        log_blocked_attempt(command, reason, project_path)
        
        # Output error message for Claude
        error_message = f"""🚫 COMMAND BLOCKED: {reason}

This command was blocked by the PreToolUse safety hook to prevent potential damage.

Blocked command: {command}

If you need to run this command, please:
1. Verify the command is safe and intentional
2. Ask the user to run it manually in their terminal
3. Or modify the command to be less destructive (e.g., add --dry-run, use specific targets)

For more information, see: ~/.claude/hooks/blocked.log"""
        
        print(error_message, file=sys.stderr)
        sys.exit(2)  # Exit code 2 blocks the command
    else:
        # Command is safe, allow it
        sys.exit(0)

if __name__ == '__main__':
    main()
