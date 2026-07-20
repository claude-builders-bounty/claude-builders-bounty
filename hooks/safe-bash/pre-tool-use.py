#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime

def log_blocked(command: str):
    log_file = os.path.expanduser('~/.claude/hooks/blocked.log')
    pwd = os.getcwd()
    timestamp = datetime.now().isoformat()
    try:
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] BLOCKED | Project: {pwd} | Command: {command}\n")
    except Exception:
        pass

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
    
    tool_name = sys.argv[1]
    if tool_name not in ['Bash', 'run_command']:
        sys.exit(0)
        
    try:
        input_data = sys.stdin.read()
        args = json.loads(input_data)
        command = args.get('command', '') or args.get('CommandLine', '')
        
        if not command:
            sys.exit(0)
            
        command_upper = command.upper()
        
        # Check patterns
        blocked = False
        reason = ""
        
        if "RM -RF" in command_upper:
            blocked = True
            reason = "rm -rf is blocked for safety"
        elif "DROP TABLE" in command_upper:
            blocked = True
            reason = "DROP TABLE is blocked for safety"
        elif "TRUNCATE" in command_upper:
            blocked = True
            reason = "TRUNCATE is blocked for safety"
        elif "GIT PUSH --FORCE" in command_upper or "GIT PUSH -F" in command_upper:
            blocked = True
            reason = "git push --force is blocked for safety"
        elif "DELETE FROM" in command_upper and "WHERE" not in command_upper:
            blocked = True
            reason = "DELETE FROM without a WHERE clause is blocked for safety"
            
        if blocked:
            log_blocked(command)
            # Display clear message to Claude
            print(f"ERROR: Command execution blocked by security hook.")
            print(f"Reason: {reason}")
            print(f"The command '{command}' is destructive and not permitted.")
            sys.exit(1)
            
        sys.exit(0)
        
    except Exception as e:
        # Fail open if there's a parsing error so we don't break normal tools
        sys.exit(0)

if __name__ == '__main__':
    main()
