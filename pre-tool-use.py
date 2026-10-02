#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        # Claude passes the tool name as the first argument
        sys.exit(0)
        
    tool_name = sys.argv[1].lower()
    
    # We only care about tools that execute bash commands or run scripts
    if tool_name not in ["bash", "run_command", "terminal", "shell"]:
        sys.exit(0)

    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
            
        args = json.loads(input_data)
    except json.JSONDecodeError:
        # Not valid JSON, ignore
        sys.exit(0)

    # The command could be under 'command', 'script', or 'code' depending on the exact tool schema
    command = args.get("command") or args.get("script") or args.get("code") or ""
    if not isinstance(command, str) or not command.strip():
        sys.exit(0)

    blocked = False
    reason = ""

    # 1. rm -rf
    if re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b', command) or re.search(r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b', command) or re.search(r'\brm\s+-rf\b', command):
        blocked = True
        reason = "Execution of 'rm -rf' is blocked for safety."
        
    # 2. DROP TABLE
    elif re.search(r'\bDROP\s+TABLE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Execution of 'DROP TABLE' is blocked to prevent data loss."

    # 3. git push --force
    elif re.search(r'\bgit\s+push\s+.*(?:--force|-f)\b', command):
        blocked = True
        reason = "Execution of 'git push --force' is blocked to prevent overwriting history."

    # 4. TRUNCATE
    elif re.search(r'\bTRUNCATE\s+TABLE\b|\bTRUNCATE\b', command, re.IGNORECASE):
        # We need to make sure it's SQL TRUNCATE, but matching the word is usually enough for a safety hook
        blocked = True
        reason = "Execution of 'TRUNCATE' is blocked to prevent data loss."

    # 5. DELETE FROM without WHERE
    elif re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE):
        # If there is no WHERE clause after DELETE FROM
        if not re.search(r'\bWHERE\b', command, re.IGNORECASE):
            blocked = True
            reason = "Execution of 'DELETE FROM' without a 'WHERE' clause is blocked to prevent wiping entire tables."

    if blocked:
        log_dir = Path.home() / ".claude" / "hooks"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "blocked.log"
        
        timestamp = datetime.datetime.now().isoformat()
        project_path = os.getcwd()
        
        log_entry = f"[{timestamp}] BLOCKED | Project: {project_path} | Command: {command}\n"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass # Hook should not fail if it can't write to the log
            
        print(f"ERROR: Tool use blocked by pre-tool-use hook.\nReason: {reason}")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
