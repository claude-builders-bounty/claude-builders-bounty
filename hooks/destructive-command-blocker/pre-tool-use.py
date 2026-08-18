#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Blocker
Intercepts dangerous commands before execution and logs security violations.
"""

import sys
import os
import json
import re
from datetime import datetime

def log_blocked(command, reason, project_dir):
    home = os.path.expanduser("~")
    log_dir = os.path.join(home, ".claude", "hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason} | DIR: {project_dir} | CMD: {command}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Failed to write to blocked.log: {e}\n")

def check_command(command, project_dir=None):
    if not command:
        return True, None

    cmd = command.strip()

    # 1. rm -rf variants
    if re.search(r'\brm\s+', cmd, re.IGNORECASE):
        has_r = re.search(r'-[a-zA-Z]*r', cmd, re.IGNORECASE)
        has_f = re.search(r'-[a-zA-Z]*f', cmd, re.IGNORECASE)
        if has_r and has_f:
            return False, "Destructive recursive file deletion (rm -rf)"

    # 2. DROP database / table / schema
    if re.search(r'\bDROP\s+(?:DATABASE|TABLE|SCHEMA)\b', cmd, re.IGNORECASE):
        return False, "Database drop table/database/schema query"

    # 3. TRUNCATE table
    if re.search(r'\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_]+', cmd, re.IGNORECASE):
        return False, "Database table truncate query"

    # 4. DELETE FROM without WHERE
    if re.search(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE) and not re.search(r'\bWHERE\b', cmd, re.IGNORECASE):
        return False, "Unbounded DELETE FROM query without a WHERE clause"

    # 5. git push --force / -f
    if re.search(r'\bgit\s+push\b', cmd, re.IGNORECASE) and re.search(r'(?:--force|-f\b)', cmd, re.IGNORECASE):
        return False, "Forced git push (--force / -f)"

    # 6. Filesystem formatting
    if re.search(r'\bmkfs(?:\.[a-zA-Z0-9]+)?\b', cmd, re.IGNORECASE):
        return False, "Filesystem format command (mkfs)"

    # 7. Raw disk overwriting
    if re.search(r'\bdd\s+if=/dev/(?:zero|urandom|null)\s+of=/dev/[a-zA-Z0-9]+', cmd, re.IGNORECASE):
        return False, "Direct raw disk overwriting (dd)"

    # 8. Fork bomb
    if re.search(r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', cmd):
        return False, "Fork bomb pattern"

    return True, None

def main():
    try:
        raw_input = sys.stdin.read()
        if raw_input:
            data = json.loads(raw_input)
            tool_name = data.get("tool_name", "")
            tool_input = data.get("tool_input", {})
            project_dir = data.get("cwd", os.getcwd())

            if tool_name in ["bash", "execute_command", "run_command"]:
                command = tool_input.get("command") or tool_input.get("CommandLine") or ""
                allowed, reason = check_command(command, project_dir)
                if not allowed:
                    log_blocked(command, reason, project_dir)
                    error_msg = f"⛔ COMMAND BLOCKED BY SECURITY HOOK: {reason}\nAttempted command: {command}\nThis operation is prohibited to prevent accidental data loss or destructive git/database mutations."
                    print(error_msg, file=sys.stderr)
                    sys.exit(1)
    except json.JSONDecodeError:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
