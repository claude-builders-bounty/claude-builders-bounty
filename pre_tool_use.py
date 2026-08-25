#!/usr/bin/env python3
"""Pre-tool-use hook that blocks destructive bash commands.
Install: mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use.py
Config: Add to ~/.claude/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "~/.claude/hooks/pre_tool_use.py"}]
    }]
  }
}
"""
import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    (r'rm\s+-rf\s+/', 'Recursive force delete on root or absolute path'),
    (r'rm\s+-rf\s+\$HOME', 'Recursive force delete on home directory'),
    (r'rm\s+-rf\s+\~', 'Recursive force delete on home directory'),
    (r'DROP\s+TABLE', 'SQL DROP TABLE statement'),
    (r'TRUNCATE\s+TABLE', 'SQL TRUNCATE TABLE statement'),
    (r'DELETE\s+FROM\s+\w+\s*(?!WHERE)', 'DELETE FROM without WHERE clause'),
    (r'git\s+push\s+--force', 'Git force push'),
    (r'git\s+push\s+-f\b', 'Git force push (short)'),
    (r'>\s*/dev/sd[a-z]', 'Writing to block device'),
    (r'mkfs\.', 'Filesystem formatting'),
    (r'dd\s+if=.*of=/dev/', 'dd writing to device'),
    (r':(){ :|:& };:', 'Fork bomb'),
    (r'chmod\s+-R\s+777\s+/', 'Recursive chmod 777 on root'),
    (r'chown\s+-R\s+.*\s+/ ', 'Recursive chown on root'),
]

# Patterns that are OK (allowlist)
ALLOWED_PATTERNS = [
    r'rm\s+-rf\s+\.git',  # Cleaning git dirs
    r'rm\s+-rf\s+node_modules',  # Cleaning node_modules
    r'rm\s+-rf\s+dist',  # Cleaning dist
    r'rm\s+-rf\s+build',  # Cleaning build
    r'rm\s+-rf\s+\.next',  # Cleaning .next
    r'rm\s+-rf\s+coverage',  # Cleaning coverage
    r'rm\s+-rf\s+__pycache__',  # Cleaning pycache
    r'rm\s+-rf\s+\.pytest_cache',  # Cleaning pytest cache
    r'git\s+push\s+--force-with-lease',  # Safer force push
]

LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def is_blocked(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked pattern."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check if it's explicitly allowed
            for allowed in ALLOWED_PATTERNS:
                if re.search(allowed, command, re.IGNORECASE):
                    return False, ''
            return True, reason
    return False, ''

def log_blocked(command: str, reason: str, project_path: str):
    """Log blocked attempt to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'command': command,
        'reason': reason,
        'project_path': project_path,
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def main():
    # Read tool input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not JSON, pass through
        sys.exit(0)
    
    # Only process Bash tool calls
    tool_name = input_data.get('tool_name', '')
    if tool_name != 'Bash':
        sys.exit(0)
    
    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')
    project_path = tool_input.get('cwd', os.getcwd())
    
    if not command:
        sys.exit(0)
    
    blocked, reason = is_blocked(command)
    
    if blocked:
        log_blocked(command, reason, project_path)
        
        # Return error to Claude
        output = {
            'decision': 'block',
            'reason': f'BLOCKED: {reason}\n\nCommand: {command}\n\nThis command was blocked by the safety hook. If this was a legitimate operation, please rephrase or use a safer alternative.\n\nLogged to: {LOG_FILE}'
        }
        print(json.dumps(output))
        sys.exit(2)  # Exit code 2 = block
    
    # Allow the command
    sys.exit(0)

if __name__ == '__main__':
    main()