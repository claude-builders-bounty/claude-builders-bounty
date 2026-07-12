#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.
"""

import json
import sys
import os
from datetime import datetime

def log_blocked_command(command, project_path):
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create the log entry
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path
    }
    
    # Write to log file
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"{timestamp} - Blocked command: {command} in {project_path}\n")

def is_dangerous_command(command):
    """Check if command matches any dangerous patterns"""
    dangerous_patterns = [
        'rm -rf',
        'DROP TABLE',
        'git push --force',
        'TRUNCATE',
        'DELETE FROM'
    ]
    
    # Check for DELETE FROM without WHERE
    if 'DELETE FROM' in command and 'WHERE' not in command.upper():
        return True
        
    # Check other dangerous patterns
    for pattern in dangerous_patterns:
        if pattern in command:
            return True
    return False

def main():
    # Read the input
    input_data = json.loads(sys.stdin.read())
    tool_name = input_data.get('tool_name')
    tool_input = input_data.get('tool_input', {})
    
    # Only handle bash commands
    if tool_name == 'bash' and is_dangerous_command(tool_input.get('command', '')):
        log_blocked_command(tool_input.get('command', ''), os.getcwd())
        print("❌ CLAUDE: This command has been blocked as potentially destructive.")
        print(f"Blocked: {tool_input.get('command')}")
        print("Blocked command logged to ~/.claude/hooks/blocked.log")
        sys.exit(1)
        
    # If we get here, the command is safe to execute
    print(json.dumps(input_data))

if __name__ == "__main__":
    main()