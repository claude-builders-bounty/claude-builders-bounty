#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime

def log_blocked(command, project_path):
    """Logs blocked attempts to ~/.claude/hooks/blocked.log"""
    hook_dir = os.path.expanduser("~/.claude/hooks")
    log_file = os.path.join(hook_dir, "blocked.log")
    try:
        os.makedirs(hook_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] BLOCKED: {command} | PATH: {project_path}\n")
    except Exception:
        pass

def check_command(command):
    """Checks if the command matches any destructive patterns."""
    # 1. rm -rf
    if re.search(r"rm\s+-rf", command, re.IGNORECASE):
        return "rm -rf is a destructive command."
    
    # 2. DROP TABLE
    if re.search(r"DROP\s+TABLE", command, re.IGNORECASE):
        return "DROP TABLE is a destructive SQL command."
    
    # 3. git push --force
    if re.search(r"git\s+push\s+--force", command, re.IGNORECASE):
        return "git push --force is dangerous."
    
    # 4. TRUNCATE
    if re.search(r"TRUNCATE", command, re.IGNORECASE):
        return "TRUNCATE is a destructive SQL command."
    
    # 5. DELETE FROM without WHERE
    if re.search(r"DELETE\s+FROM", command, re.IGNORECASE):
        if not re.search(r"WHERE", command, re.IGNORECASE):
            return "DELETE FROM without a WHERE clause is dangerous."
    
    return None

def main():
    try:
        # Claude Code hooks receive tool call info via stdin
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
        
        data = json.loads(input_data)
        tool_name = data.get("tool")
        arguments = data.get("arguments", {})
        
        # We target bash and shell tools
        if tool_name in ["bash", "shell"]:
            command = arguments.get("command", "")
            if not command:
                sys.exit(0)
            
            project_path = os.getcwd()
            reason = check_command(command)
            
            if reason:
                log_blocked(command, project_path)
                # Print to stderr so Claude sees the error message
                print(f"\n[SECURITY BLOCK] {reason}", file=sys.stderr)
                # Exit with non-zero to block the tool execution
                sys.exit(1)
                
    except json.JSONDecodeError:
        # Not a JSON tool call, ignore
        sys.exit(0)
    except Exception:
        # Fail open on unexpected errors to avoid breaking Claude
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()