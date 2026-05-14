#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
        
    tool_name = sys.argv[1]
    
    # Check if the tool is Bash or related to running commands
    if tool_name not in ["Bash", "run_command", "RunCommand"]:
        sys.exit(0)

    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
        payload = json.loads(input_data)
    except Exception:
        sys.exit(0)

    # Claude Code typically sends {"command": "..."} for Bash
    command = payload.get("command", "")
    if not command:
        sys.exit(0)

    patterns = [
        (r'rm\s+-[A-Za-z]*r[A-Za-z]*f|rm\s+-[A-Za-z]*f[A-Za-z]*r', "rm -rf"),
        (r'git\s+push\s+(.*\s+)?(--force|-f)(\s|$)', "git push --force"),
        (r'(?i)\bDROP\s+TABLE\b', "DROP TABLE"),
        (r'(?i)\bTRUNCATE\s+(TABLE)?\b', "TRUNCATE"),
    ]

    blocked = False
    reason = ""

    for pattern, name in patterns:
        if re.search(pattern, command):
            blocked = True
            reason = f"Dangerous command: {name}"
            break

    if not blocked and re.search(r'(?i)\bDELETE\s+FROM\b', command) and not re.search(r'(?i)\bWHERE\b', command):
        blocked = True
        reason = "Dangerous database command: DELETE FROM without WHERE clause"

    if blocked:
        hook_dir = os.path.expanduser("~/.claude/hooks")
        os.makedirs(hook_dir, exist_ok=True)
        log_file = os.path.join(hook_dir, "blocked.log")
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_path = os.getcwd()
        
        with open(log_file, "a") as f:
            safe_command = command.replace('\n', ' ')
            f.write(f"[{timestamp}] [Path: {project_path}] [Command: {safe_command}] [Reason: {reason}]\n")
        
        print("❌ ERROR: Command execution blocked by pre-tool-use safety hook.")
        print(f"Reason: {reason}")
        print(f"This incident has been logged to {log_file}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
