#!/usr/bin/env python3
import os
import sys
import re
import json
import datetime
from pathlib import Path

def extract_command():
    # Claude Code passes tool arguments to pre-tool-use hooks via CLAUDE_TOOL_ARGS
    tool_args = os.environ.get('CLAUDE_TOOL_ARGS', '')
    try:
        data = json.loads(tool_args)
        if 'command' in data:
            return data['command']
    except:
        pass
    
    # Fallback to checking all arguments and stdin
    cmd = " ".join(sys.argv[1:])
    if not sys.stdin.isatty():
        cmd += " " + sys.stdin.read()
    return cmd

def log_blocked(command):
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    
    timestamp = datetime.datetime.now().isoformat()
    project_path = os.getcwd()
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Project: {project_path} | Blocked: {command}\n")

def main():
    command = extract_command()
    if not command:
        sys.exit(0)
        
    cmd_upper = command.upper()
    
    # 1. rm -rf
    if re.search(r'\brm\s+-r[fF]?\b|\brm\s+-f[rR]?\b', command):
        blocked = True
    # 2. DROP TABLE
    elif "DROP TABLE" in cmd_upper:
        blocked = True
    # 3. git push --force
    elif re.search(r'\bgit\s+push\s+(.*\s)?(--force|-f)\b', command):
        blocked = True
    # 4. TRUNCATE
    elif "TRUNCATE" in cmd_upper:
        blocked = True
    # 5. DELETE FROM without WHERE
    elif "DELETE FROM" in cmd_upper and "WHERE" not in cmd_upper:
        blocked = True
    else:
        sys.exit(0) # Not blocked, allow execution
        
    log_blocked(command)
    print("❌ ERROR: Command blocked by Claude Code security hook.")
    print(f"Reason: Your command matched a destructive pattern blocklist (e.g., rm -rf, DROP TABLE, force push, etc).")
    print("Please revise your command or ask the user to perform this action manually.")
    sys.exit(1)

if __name__ == "__main__":
    main()
