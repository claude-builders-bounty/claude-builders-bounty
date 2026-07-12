#!/usr/bin/env python3

import os
import sys
import re
from datetime import datetime

def check_and_block_command():
    # Read the command from stdin
    command = sys.stdin.read().strip()
    
    # Dangerous patterns to block
    dangerous_patterns = [
        r'rm\s+-rf',
        r'DROP\s+TABLE',
        b'git push --force',
        r'TRUNCATE',
        r'DELETE\s+FROM\s+\w+\s*$',  # DELETE without WHERE clause
        r'DELETE\s+FROM\s+\w+\s*;'     # Handle semicolon termination
    ]
    
    # Check if command matches any dangerous pattern
    is_dangerous = False
    for pattern in dangerous_patterns:
        if re.search(r'DELETE\s+FROM', pattern, re.IGNORECASE) and 'WHERE' not in command.upper():
            is_dangerous = True
            break
        elif re.search(pattern, command, re.IGNORECASE):
            is_dangerous = True
            break

    if is_dangerous:
        # Log the blocked attempt
        home_dir = os.path.expanduser('~')
        log_path = os.path.join(home_dir, '.claude', 'hooks', 'blocked.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f'{timestamp} - Blocked command: {command}\n')
        
        # Print explanation to stderr (which will be shown to Claude)
        print(f"Command blocked for security reasons: {command}", file=sys.stderr)
        sys.exit(1)  # Exit with error code to prevent command execution
    
    # If we get here, the command is safe to execute
    print(command)  # Echo the command back to the original process

if __name__ == "__main__":
    check_and_block_command()