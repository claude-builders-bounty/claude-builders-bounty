#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime

def block_destructive_commands():
    # Get the command from Claude Code
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    
    # Destructive patterns to block
    blocked_patterns = [
        r"rm\s+-rf",
        r"DROP\s+TABLE",
        r"git\s+push\s+--force",
        r"TRUNCATE\s+TABLE",
        r"DELETE\s+FROM(?!\s+\w+\s+WHERE\b)",
    ]
    
    # Check if command matches any blocked pattern
    for pattern in blocked_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            # Log the blocked attempt
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            project_path = os.getcwd()
            log_entry = f"[{timestamp}] Blocked command: {command} (Project: {project_path})\n"
            
            # Append to blocked.log
            log_file = os.path.expanduser("~/.claude/hooks/blocke d.log")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, "a") as f:
                f.write(log_entry)
            
            # Inform Claude about the block
            print(f"🚫 Blocked destructive command: {command}", file=sys.stderr)
            print("This command has been blocked for security reasons.", file=sys.stderr)
            print("The following patterns are blocked:")
            print("- rm -rf")
            print("- DROP TABLE")
            print("- git push --force")
            print("- TRUNCATE")
            print("- DELETE FROM (without WHERE clause)")
            print("Contact: claudebounty@gmail.com")
            sys.exit(1)
    
    # If we get here, the command is allowed
    sys.exit(0)

if __name__ == "__main__":
    block_destructive_commands()