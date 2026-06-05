#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

def log_blocked_attempt(command, project_path):
    log_dir = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] Command: {command} | Project: {project_path}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)

def main():
    try:
        # Read JSON context from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            sys.exit(0)
            
        data = json.loads(input_data)
        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input") or {}
        
        # We only check Bash tool commands
        if tool_name != "Bash":
            sys.exit(0)
            
        command = tool_input.get("command", "")
        project_path = os.getcwd()
        
        # Block patterns
        blocked_patterns = [
            r"rm\s+-rf",
            r"(?i)drop\s+table",
            r"git\s+push\s+.*--force",
            r"(?i)truncate"
        ]
        
        is_blocked = False
        reason = ""
        
        # Check standard patterns
        for pat in blocked_patterns:
            if re.search(pat, command):
                is_blocked = True
                reason = f"matches dangerous pattern: {pat}"
                break
                
        # Special check: DELETE FROM without a WHERE clause
        if not is_blocked and re.search(r"(?i)delete\s+from", command):
            if not re.search(r"(?i)where", command):
                is_blocked = True
                reason = "DELETE FROM command missing WHERE clause"
                
        if is_blocked:
            log_blocked_attempt(command, project_path)
            # Display helpful error message to Claude explaining why it was blocked
            print(f"\n[SECURITY BLOCK] Command execution denied: {reason}.", file=sys.stderr)
            print(f"Blocked Command: {command}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        # Avoid blocking standard commands if hook fails unexpectedly
        pass
        
    sys.exit(0)

if __name__ == "__main__":
    main()
