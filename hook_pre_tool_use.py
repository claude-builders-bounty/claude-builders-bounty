#!/usr/bin/env python3

import json
import sys
import os
import time
from pathlib import Path

def block_destructive_commands():
    """Pre-tool-use hook that blocks destructive bash commands"""
    
    # Read the tool use request from stdin
    input_data = sys.stdin.read()
    if not input_data:
        return
    
    try:
        tool_use = json.loads(input_data)
    except json.JSONDecodeError:
        # If not JSON, treat as a regular command
        command = input_data.strip()
        check_and_block_command(command)
        return
    
    # Check if this is a bash tool use
    if tool_use.get("tool") != "bash":
        print(input_data)  # Echo back non-bash tool uses
        return
    
    command = tool_use.get("command", "").strip()
    check_and_block_command(command)

def check_and_block_command(command):
    """Check a command and block if it's destructive"""
    # List of destructive patterns to block
    destructive_patterns = [
        "rm -rf",
        "DROP TABLE",
        "git push --force",
        "TRUNCATE ",
        "DELETE FROM "
    ]
    
    # Special handling for DELETE FROM without WHERE
    if "DELETE FROM" in command and "WHERE" not in command.upper():
        log_blocked_command(command)
        print(f"❌ Command blocked: DELETE statements without WHERE clause are destructive", file=sys.stderr)
        sys.exit(1)
    
    # Check for other destructive patterns
    for pattern in destructive_patterns:
        if pattern in command:
            log_blocked_command(command)
            if pattern == "DELETE FROM ":
                print(f"❌ Command blocked: DELETE statements without WHERE clause are destructive", file=sys.stderr)
            else:
                print(f"❌ Command blocked: {pattern} is a destructive command pattern", file=sys.stderr)
            sys.exit(1)
    
    # If we get here, echo the original input (non-destructive)
    print(command)

def get_project_path():
    """Get the current project path"""
    # In a real implementation, this would determine the project path
    # For now we'll use a placeholder
    return os.getcwd()

def log_blocked_command(command):
    """Log blocked command attempts"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    project_path = get_project_path()
    
    # Create the hooks directory if it doesn't exist
    log_file_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file_path, "a") as f:
        f.write(f"[{timestamp}] Blocked: {command} in {project_path}\n")

if __name__ == "__main__":
    block_destructive_commands()