#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime

def main():
    try:
        payload = sys.stdin.read()
        if not payload:
            sys.exit(0)
        data = json.loads(payload)
    except Exception:
        sys.exit(0)

    # Claude Code passes toolName and toolInput
    tool_name = data.get("toolName", "")
    tool_input = data.get("toolInput", {})
    
    # We only care about Bash/Command tools
    if tool_name not in ["Bash", "Command"]:
        sys.exit(0)
        
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked = False
    reason = ""
    cmd_upper = command.upper()
    
    # Check rm -rf
    if re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f', command) or \
       re.search(r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r', command) or \
       re.search(r'\brm\s+-[rR]\s+-f', command) or \
       'rm -rf' in command or 'rm -fr' in command:
        blocked = True
        reason = "Blocked dangerous command: 'rm -rf'"
        
    # Check DROP TABLE
    elif "DROP TABLE" in cmd_upper:
        blocked = True
        reason = "Blocked dangerous database command: 'DROP TABLE'"
        
    # Check TRUNCATE
    elif "TRUNCATE" in cmd_upper:
        blocked = True
        reason = "Blocked dangerous database command: 'TRUNCATE'"
        
    # Check DELETE FROM without WHERE
    elif "DELETE FROM" in cmd_upper and "WHERE" not in cmd_upper:
        blocked = True
        reason = "Blocked dangerous database command: 'DELETE FROM' without a 'WHERE' clause"
        
    # Check git push --force
    elif "git push" in command and ("--force" in command or "-f" in command.split()):
        blocked = True
        reason = "Blocked dangerous command: 'git push --force'"
        
    if blocked:
        # Log the blocked attempt
        log_dir = os.path.expanduser("~/.claude/hooks")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "blocked.log")
        
        project_path = os.getcwd()
        timestamp = datetime.now().isoformat()
        
        try:
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] Project: {project_path} | Command: {command}\n")
        except:
            pass
            
        # Display clear message to Claude
        print(f"ERROR: {reason}. This action is prohibited by the security hook.")
        # Exit with a non-zero code to actually block the execution in Claude Code
        sys.exit(1)
        
    # Allow command
    sys.exit(0)

if __name__ == "__main__":
    main()
