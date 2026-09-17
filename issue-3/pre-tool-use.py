#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

def is_dangerous(cmd):
    # Regex patterns for dangerous commands
    patterns = [
        r'\brm\s+-r[fF]?\b',                 # rm -rf, rm -r, rm -fr
        r'\bDROP\s+TABLE\b',                 # DROP TABLE
        r'\bgit\s+push\s+--force\b',         # git push --force
        r'\bgit\s+push\s+-f\b',              # git push -f
        r'\bTRUNCATE\b',                     # TRUNCATE
    ]
    
    # Check for DELETE FROM without WHERE
    if re.search(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', cmd, re.IGNORECASE):
            return True, "DELETE FROM without a WHERE clause"
            
    for p in patterns:
        if re.search(p, cmd, re.IGNORECASE):
            return True, f"Matched dangerous pattern: {p.replace(chr(92), '')}"
            
    return False, ""

def log_blocked(cmd):
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    cwd = os.getcwd()
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Project: {cwd} | Command: {cmd}\n")

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
        
    tool_name = sys.argv[1]
    
    # Only care about bash command execution
    if tool_name != "BashCommand":
        sys.exit(0)
        
    try:
        # Claude passes arguments as JSON via stdin
        input_data = sys.stdin.read()
        args = json.loads(input_data)
        
        cmd = args.get("command", "")
        
        dangerous, reason = is_dangerous(cmd)
        
        if dangerous:
            log_blocked(cmd)
            # Output error back to Claude
            print(json.dumps({
                "status": "blocked",
                "message": f"CRITICAL: The command '{cmd}' was blocked for safety reasons ({reason}). Do NOT attempt to run this command without user consent or modifying it to be safe."
            }))
            sys.exit(1)
            
        sys.exit(0)
        
    except Exception as e:
        # Failsafe: don't block if there's a parsing error
        sys.exit(0)

if __name__ == "__main__":
    main()
