#!/usr/bin/env python3
import sys
import json
import re
import datetime
import os

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command, project_path):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] Project: {project_path} | Blocked command: {command}\n")

def main():
    try:
        # Read JSON payload from stdin
        input_data = sys.stdin.read()
        if not input_data:
            return 0
            
        payload = json.loads(input_data)
        
        # We only care about Bash tool
        if payload.get("toolName") != "Bash" and payload.get("tool_name") != "Bash":
            return 0
            
        # Try to get command from tool_input or toolParameters
        tool_input = payload.get("tool_input", payload.get("toolParameters", {}))
        command = tool_input.get("command", "")
        
        if not command:
            return 0
            
        # Destructive patterns
        patterns = [
            (r"\brm\s+-rf\b", "rm -rf"),
            (r"(?i)\bDROP\s+TABLE\b", "DROP TABLE"),
            (r"\bgit\s+push\s+--force\b", "git push --force"),
            (r"(?i)\bTRUNCATE\b", "TRUNCATE")
        ]
        
        # Check DELETE FROM without WHERE manually
        if re.search(r"(?i)\bDELETE\s+FROM\b", command) and not re.search(r"(?i)\bWHERE\b", command):
            project_path = payload.get("project_path", os.getcwd())
            log_blocked(command, project_path)
            print("Error: Command blocked by safety hook. The use of 'DELETE FROM without WHERE clause' is strictly prohibited.", file=sys.stderr)
            sys.exit(2)
        
        for pattern, name in patterns:
            if re.search(pattern, command):
                # We block the command
                project_path = payload.get("project_path", os.getcwd())
                log_blocked(command, project_path)
                
                # Send error message to Claude
                print(f"Error: Command blocked by safety hook. The use of '{name}' is strictly prohibited.", file=sys.stderr)
                # Exit 2 tells Claude Code to block execution
                sys.exit(2)
                
        # If it's fine, exit 0
        sys.exit(0)
        
    except Exception as e:
        # If something fails, do not block (or block, depending on security stance)
        # Let's not interfere with normal operation if parser fails
        sys.exit(0)

if __name__ == "__main__":
    main()
