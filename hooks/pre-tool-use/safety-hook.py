#!/usr/bin/env python3
"""
Safety hook for Claude Code that blocks dangerous bash commands.
Installs to ~/.claude/hooks/pre-tool-use/
"""

import sys
import re
import os
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf can delete important files'),
    (r'\brm\s+-r\s+-f\b', 'rm -r -f can delete important files'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE can destroy database'),
    (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE removes all data'),
    (r'\bDELETE\s+FROM\b', 'DELETE FROM needs WHERE clause'),
    (r'\bgit\s+push\s+--force\b', 'force push can overwrite history'),
    (r'\bgit\s+push\s+-f\b', 'force push can overwrite history'),
]

# Log file
LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def log_blocked(command, reason, project_path):
    """Log blocked command to file"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | {project_path} | {command} | {reason}\n"

    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def check_command(command, project_path):
    """Check if command is dangerous"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check for WHERE clause in DELETE
            if 'DELETE FROM' in command.upper():
                if 'WHERE' not in command.upper():
                    return False, reason
                continue

            return False, reason

    return True, None

def main():
    """Main hook function"""
    # Read input from Claude Code
    try:
        input_data = sys.stdin.read()
        data = eval(input_data)  # Claude Code sends Python dict
    except:
        # If can't parse, allow by default
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    project_path = data.get('project_path', os.getcwd())

    # Only check Bash tool
    if tool_name != 'Bash':
        sys.exit(0)

    command = tool_input.get('command', '')
    if not command:
        sys.exit(0)

    # Check command
    safe, reason = check_command(command, project_path)

    if not safe:
        # Log the attempt
        log_blocked(command, reason, project_path)

        # Tell Claude why it's blocked
        print(f"BLOCKED: {reason}")
        print(f"Command '{command}' has been blocked for safety.")
        print(f"Logged to {LOG_FILE}")

        # Exit with non-zero to block
        sys.exit(1)

    # Command is safe, allow execution
    sys.exit(0)

if __name__ == '__main__':
    main()
