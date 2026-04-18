#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
            
        payload = json.loads(input_data)
        
        tool_input = payload.get("tool_input", {})
        command = tool_input.get("command", "")
        
        if not command:
            sys.exit(0)

        # 1. rm -rf (handles -rf, -fr, and spaces)
        if re.search(r'rm\s+-(?:[A-Za-z]*r[A-Za-z]*f|f[A-Za-z]*r|rf|fr)\b', command):
            block(command, "Contains 'rm -rf' (recursive force removal)")
        
        # 2. DROP TABLE
        if re.search(r'(?i)\bDROP\s+TABLE\b', command):
            block(command, "Contains 'DROP TABLE'")
            
        # 3. git push --force
        if re.search(r'git\s+push\s+(?:-\S*\s+)*--force\b|git\s+push\s+-f\b', command):
            block(command, "Contains 'git push --force'")
            
        # 4. TRUNCATE
        if re.search(r'(?i)\bTRUNCATE\b', command):
            block(command, "Contains 'TRUNCATE'")
            
        # 5. DELETE FROM without WHERE clause
        if re.search(r'(?i)\bDELETE\s+FROM\b', command) and not re.search(r'(?i)\bWHERE\b', command):
            block(command, "Contains 'DELETE FROM' without a 'WHERE' clause")
            
        # If we reach here, the command is safe
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Not a valid JSON, let it pass
        sys.exit(0)
    except Exception as e:
        # Fail open so we don't interfere with normal workflow on unexpected errors
        sys.exit(0)

def block(command, reason):
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    timestamp = datetime.datetime.now().isoformat()
    project_path = os.getcwd()
    
    # Log the blocked attempt
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] COMMAND: {command!r} | PROJECT: {project_path} | REASON: {reason}\n")
        
    # Display clear message to Claude
    print(f"Command blocked by destructive-command-hook: {reason}", file=sys.stderr)
    
    # Exit with code 2 to explicitly stop the tool use (or code 1)
    sys.exit(2)

if __name__ == "__main__":
    main()
