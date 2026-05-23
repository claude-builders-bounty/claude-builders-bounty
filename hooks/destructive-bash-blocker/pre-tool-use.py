#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

def log_blocked(command, reason):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "blocked.log")
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    project_path = os.getcwd()
    log_entry = f"[{timestamp}] Project: {project_path} | Command: {command.strip()} | Reason: {reason}\n"
    with open(log_path, "a") as f:
        f.write(log_entry)

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
            
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            # Fallback to raw string command
            data = {"tool_name": "Bash", "tool_input": {"command": input_data}}
            
        command = ""
        tool_input = data.get("tool_input", {})
        if isinstance(tool_input, dict):
            command = tool_input.get("command", "")
        elif isinstance(tool_input, str):
            command = tool_input
            
        if not command:
            command = data.get("command", "")
            
        if not command:
            sys.stdout.write(input_data)
            sys.exit(0)
            
        blocked = False
        reason = ""
        
        # 1. rm -rf
        if re.search(r"\brm\s+-[a-zA-Z]*rf[a-zA-Z]*\b", command) or "rm -rf" in command:
            blocked = True
            reason = "rm -rf pattern detected"
            
        # 2. DROP TABLE
        elif re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE):
            blocked = True
            reason = "DROP TABLE pattern detected"
            
        # 3. git push --force (or -f)
        elif re.search(r"\bgit\s+push\b.*?(?:--force|\s-f\b)", command):
            blocked = True
            reason = "git push --force pattern detected"
            
        # 4. TRUNCATE
        elif re.search(r"\bTRUNCATE\b", command, re.IGNORECASE):
            blocked = True
            reason = "TRUNCATE pattern detected"
            
        # 5. DELETE FROM without WHERE
        elif re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", command, re.IGNORECASE):
                blocked = True
                reason = "DELETE FROM without WHERE clause detected"
                
        if blocked:
            log_blocked(command, reason)
            sys.stderr.write(f"ERROR: Command execution blocked by security hook.\n")
            sys.stderr.write(f"Reason: {reason}\n")
            sys.stderr.write(f"Attempted command: {command.strip()}\n")
            sys.exit(2)
            
        # Not blocked
        sys.stdout.write(input_data)
        sys.exit(0)
        
    except Exception as e:
        sys.exit(0)

if __name__ == "__main__":
    main()
