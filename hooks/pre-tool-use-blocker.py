#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.
"""

import os
import json
import re
import sys
from datetime import datetime
from pathlib import Path

def is_dangerous_command(command: str) -> bool:
    dangerous_patterns = [
        r'rm\s+-rf',
        r'DROP\s+TABLE',
        r'git\s+push\s+--force',
        r'TRUNCATE',
        r'DELETE\s+FROM\s+\S+\s*;?\s*$'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def main():
    hook_input = json.loads(sys.stdin.read())
    tool_name = hook_name = hook_input.get("tool_name")
    tool_args = hook_input.get("tool_arguments", {})
    
    if tool_name != "execute_bash":
        # Only intercept bash commands
        print(json.dumps(hook_input))
        return
        
    command = tool_args.get("command", "")
    
    if is_dangerous_command(command):
        # Log the blocked command
        log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_path = os.getcwd()
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] Command '{command}' blocked in {project_path}\n")
        
        # Block the command and inform Claude
        print("❌ Command blocked by security policy")
        sys.exit(1)
    else:
        # Allow safe commands to pass through
        print(json.dumps(hook_input))

if __name__ == "__main__":
    main()