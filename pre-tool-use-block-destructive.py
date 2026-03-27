#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.
Bounty: $100 - claude-builders-bounty/claude-builders-bounty/issues/3
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    # File system destruction
    (r'rm\s+-rf', 'rm -rf (recursive force delete)'),
    (r'rm\s+.*\s+-rf', 'rm with -rf flag'),
    (r':\s*>\s*\w+', 'file truncation with :>'),
    (r'dd\s+.*if=/dev/', 'dd with /dev input (disk destruction)'),
    
    # Database destruction
    (r'DROP\s+TABLE', 'DROP TABLE (database table deletion)'),
    (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE (database table truncation)'),
    
    # Git destruction
    (r'git\s+push\s+.*--force', 'git push --force (force push)'),
    (r'git\s+push\s+.*-f', 'git push -f (force push)'),
    (r'git\s+reset\s+.*--hard', 'git reset --hard (hard reset)'),
    
    # System commands
    (r'mkfs\.', 'mkfs (filesystem format)'),
    (r'fdisk\s+.*/dev/', 'fdisk on device'),
    (r'chmod\s+.*777', 'chmod 777 (insecure permissions)'),
    
    # Shell destruction
    (r':\(\)\{.*:\|:&\};:', 'fork bomb'),
    (r'mv\s+.*/\s+', 'mv to root'),
    (r'>/dev/sd', 'write to disk device'),
]

def log_blocked_attempt(command, reason, project_path):
    """Log blocked command attempts."""
    log_dir = Path.home() / '.claude' / 'hooks'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / 'blocked.log'
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'command': command,
        'reason': reason,
        'project_path': project_path,
        'hook': 'pre-tool-use-block-destructive'
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

def check_command(command):
    """Check if command contains dangerous patterns."""
    command_lower = command.lower()
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower, re.IGNORECASE):
            return False, reason
    
    # Additional check for DELETE FROM without WHERE
    # First check if it's a DELETE FROM command
    delete_match = re.search(r'delete\s+from\s+\w+', command_lower, re.IGNORECASE)
    if delete_match:
        # Get everything after DELETE FROM table_name
        after_delete = command_lower[delete_match.end():].strip()
        # Check if there's a WHERE clause somewhere after
        if not re.search(r'\bwhere\b', after_delete, re.IGNORECASE):
            return False, 'DELETE FROM without WHERE clause'
    
    return True, None

def main():
    # Read the tool use request from stdin
    try:
        request = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # If no valid JSON, allow the command
        print(json.dumps({'allow': True}))
        return
    
    tool_name = request.get('tool', {}).get('name', '')
    command = request.get('tool', {}).get('arguments', {}).get('command', '')
    
    if tool_name != 'exec' or not command:
        # Not an exec command, allow it
        print(json.dumps({'allow': True}))
        return
    
    # Get project path from environment or request
    project_path = request.get('context', {}).get('project_path', os.getcwd())
    
    # Check the command
    is_safe, reason = check_command(command)
    
    if not is_safe:
        # Log the blocked attempt
        log_blocked_attempt(command, reason, project_path)
        
        # Return block response with explanation
        response = {
            'allow': False,
            'message': f'🚫 Command blocked by security hook: {reason}\n\n'
                      f'Command: {command}\n\n'
                      f'This command could cause data loss or system damage.\n'
                      f'If this is intentional, please:\n'
                      f'1. Review the command carefully\n'
                      f'2. Consider safer alternatives\n'
                      f'3. Contact your administrator if needed\n\n'
                      f'Blocked commands logged to: ~/.claude/hooks/blocked.log'
        }
        print(json.dumps(response))
        return
    
    # Command is safe, allow it
    print(json.dumps({'allow': True}))

if __name__ == '__main__':
    main()