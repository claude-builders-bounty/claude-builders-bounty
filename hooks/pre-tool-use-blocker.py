#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Blocks dangerous bash commands before execution.

Installation: Copy to ~/.claude/hooks/pre-tool-use
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    # File system destruction
    (r'rm\s+-rf?', 'rm -rf: Recursive force delete'),
    (r'rm\s+.*--no-preserve-root', 'rm with --no-preserve-root'),
    
    # Database destruction
    (r'DROP\s+TABLE', 'DROP TABLE: Database table deletion'),
    (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE: Table data deletion'),
    (r'DELETE\s+FROM\s+\w+\s*;?$', 'DELETE FROM without WHERE clause'),
    (r'DELETE\s+FROM\s+\w+\s*$', 'DELETE FROM without WHERE clause'),
    
    # Git destructive operations
    (r'git\s+push\s+.*--force', 'git push --force: Force push'),
    (r'git\s+push\s+.*-f\s', 'git push -f: Force push'),
    
    # System-level dangerous commands
    (r':\(\s*\)\s*\{\s*:\|\:&\s*\};\s*:', 'Fork bomb detected'),
    (r'mkfs\.', 'mkfs: Filesystem formatting'),
    (r'dd\s+if=.*of=/dev/[sh]d', 'dd to block device'),
    (r'>\s*/dev/[sh]d', 'Direct write to block device'),
    (r'mv\s+/\s+', 'mv on root directory'),
]

# Log file path
LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'


def log_blocked_attempt(command: str, reason: str, project_path: str):
    """Log blocked command to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += "-" * 50 + "\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)


def check_command_dangerous(command: str) -> tuple[bool, str]:
    """
    Check if a command matches dangerous patterns.
    Returns (is_dangerous, reason)
    """
    command_lower = command.lower()
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower, re.IGNORECASE):
            return True, reason
    
    return False, ""


def main():
    """Main hook entry point."""
    # Read input from Claude Code
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not a valid JSON, pass through
        print(json.dumps({"allow": True}))
        return
    
    # Only check bash tool
    tool_name = input_data.get('tool', '')
    if tool_name != 'bash':
        print(json.dumps({"allow": True}))
        return
    
    # Get command and project path
    command = input_data.get('input', {}).get('command', '')
    project_path = input_data.get('project_path', os.getcwd())
    
    if not command:
        print(json.dumps({"allow": True}))
        return
    
    # Check if command is dangerous
    is_dangerous, reason = check_command_dangerous(command)
    
    if is_dangerous:
        # Log the blocked attempt
        log_blocked_attempt(command, reason, project_path)
        
        # Return block response with explanation
        response = {
            "allow": False,
            "message": f"🚫 BLOCKED: {reason}\n\n"
                      f"The following command was prevented from executing:\n"
                      f"  {command}\n\n"
                      f"This is a safety measure to prevent accidental data loss.\n"
                      f"If you're sure you want to run this command, you can:\n"
                      f"  1. Modify the command to be safer\n"
                      f"  2. Run it manually outside of Claude Code\n\n"
                      f"Blocked attempts are logged to: {LOG_FILE}"
        }
        print(json.dumps(response))
        return
    
    # Command is safe, allow it
    print(json.dumps({"allow": True}))


if __name__ == '__main__':
    main()
