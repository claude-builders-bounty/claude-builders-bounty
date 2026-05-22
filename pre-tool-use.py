#!/usr/bin/env python3

import sys
import json
import os
import re
from datetime import datetime

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

# Setup log directory
os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)

def log_blocked(command):
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()
    with open(BLOCKED_LOG, "a") as f:
        f.write(f"[{timestamp}] [{project_path}] Blocked: {command}\n")

def check_command(command):
    patterns = [
        r"rm\s+-r?[fF]",
        r"DROP\s+TABLE",
        r"git\s+push\s+--force",
        r"TRUNCATE",
        # DELETE FROM without WHERE (case insensitive, multiline)
        r"(?i)DELETE\s+FROM\s+[a-zA-Z0-9_]+\s*(?!.*WHERE)"
    ]
    
    for pattern in patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
            
        request = json.loads(input_data)
        
        # We only care about tool use
        if request.get("type") != "tool_use" or request.get("tool", {}).get("name") not in ["run_command", "bash"]:
            # Accept
            print(json.dumps({"status": "accept"}))
            sys.exit(0)
            
        # Get the command
        params = request.get("tool", {}).get("parameters", {})
        command = params.get("CommandLine", params.get("command", ""))
        
        if check_command(command):
            log_blocked(command)
            # Reject
            print(json.dumps({
                "status": "reject",
                "message": "Blocked destructive command. This pattern is forbidden for security reasons."
            }))
            sys.exit(0)
            
        # Accept
        print(json.dumps({"status": "accept"}))
        
    except Exception as e:
        # Failsafe: accept on error so we don't break Claude Code
        print(json.dumps({"status": "accept"}))

if __name__ == "__main__":
    main()
