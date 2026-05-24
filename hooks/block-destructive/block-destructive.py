#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"rm\s+--recursive\s+--force",
    r"DROP\s+TABLE",
    r"git\s+push\s+--force",
    r"git\s+push\s+-f",
    r"TRUNCATE\s+",
    r"DELETE\s+FROM\s+(?!.*\bWHERE\b)"
]

def log_blocked(command, cwd):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{cwd}] {command}\n")

def main():
    try:
        payload = json.load(sys.stdin)
        
        # Only inspect tool calls
        if payload.get("type") != "toolUse":
            print(json.dumps(payload))
            return
            
        tool = payload.get("tool", {})
        if tool.get("name") != "Bash":
            print(json.dumps(payload))
            return
            
        command = tool.get("input", {}).get("command", "")
        cwd = os.getcwd()
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                log_blocked(command, cwd)
                # Return a blocked response
                response = {
                    "type": "block",
                    "reason": f"Security Exception: Command '{command}' matched destructive pattern '{pattern}'. This command was blocked and logged to {LOG_FILE}."
                }
                print(json.dumps(response))
                return
                
        # Safe to proceed
        print(json.dumps(payload))
    except Exception as e:
        # Failsafe: block on internal error to prevent bypass
        print(json.dumps({
            "type": "block", 
            "reason": f"Hook execution failed: {str(e)}"
        }))

if __name__ == "__main__":
    main()
