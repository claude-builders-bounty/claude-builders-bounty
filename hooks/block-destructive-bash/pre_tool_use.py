#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

# Destructive command patterns to block
BLOCKED_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bDROP\s+TABLE\b",
    r"\bgit\s+push\s+--force\b",
    r"\bTRUNCATE\b",
]

def check_delete_from(cmd):
    if re.search(r"\bDELETE\s+FROM\b", cmd, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", cmd, re.IGNORECASE):
            return True
    return False

def contains_destructive_pattern(cmd):
    if check_delete_from(cmd):
        return "DELETE FROM without WHERE clause"
    
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return pattern
            
    return None

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
            
        data = json.loads(input_data)
        
        # Parse inputs
        tool_name = data.get("tool", data.get("name", ""))
        tool_input = data.get("input", {})
        
        comando = tool_input.get("command", "")
        if not comando:
            sys.exit(0)
            
        violation = contains_destructive_pattern(comando)
        
        if violation:
            # We log it
            log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            timestamp = datetime.datetime.now().isoformat()
            project_path = os.getcwd()
            
            log_entry = f"[{timestamp}] BLOCKED: '{comando}' | REASON: {violation} | PATH: {project_path}\n"
            
            with open(log_path, "a") as f:
                f.write(log_entry)
            
            # Print to stdout so Claude can see why it was blocked
            print(f"ERROR: Execution of '{comando}' was blocked by a pre-tool-use hook.")
            print(f"Reason: Detected dangerous pattern: {violation}")
            print(f"Blocked actions: rm -rf, DROP TABLE, TRUNCATE, git push --force, DELETE FROM (no WHERE).")
            
            # Exit 1 to indicate failure so Claude doesn't execute the tool
            sys.exit(1)
            
    except Exception as e:
        pass
        
    sys.exit(0)

if __name__ == "__main__":
    main()
