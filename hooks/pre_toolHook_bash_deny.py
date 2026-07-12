#!/usr/bin/env python3
import os
import json
import sys
import re

def pre_toolHook_bash_deny():
    # Read the command from stdin
    command = json.loads(sys.stdin.read())
    command_str = command['tool_input'].get('command', '') if isinstance(command.get('tool_input'), dict) else ''
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf',
        r'DROP\s+TABLE',
        r'git push --force',
        r'TRUNCATE',
        r'DELETE\s+FROM\s+\w+\s+WHERE',  # DELETE with WHERE clause
    ]
    
    # Block destructive commands
    if any(re.search(pattern, command_str) for pattern in dangerous_patterns):
        # Log the blocked command
        with open(os.path.expanduser('~/.claude/hooks/blocked.log'), 'a') as f:
            f.write(f'{command_str}\n')
        # Block the command if it contains destructive patterns
        return True
    elif command_str == 'git push --force' or command_str.startswith('DROP TABLE') or 'git push --force' in command_str or 'TRUNCATE' in command_str:
        # Block the command if it contains destructive patterns
        return True
    elif command_str == 'DELETE' and 'WHERE' not in command_str:
        # Let it pass if it doesn't contain WHERE clause
        return False
    elif command_str.startswith('rm -rf'):
        # Block the command if it starts with 'rm -rf'
        return True