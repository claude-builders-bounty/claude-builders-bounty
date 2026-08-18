#!/usr/bin/env python3
"""
Pre-Tool-Use Security Hook for Claude Code & AI Coding Agents.
Blocks destructive bash commands and SQL statements before execution.
"""

import sys
import os
import re
import json
from datetime import datetime

def log_blocked(command: str, reason: str, cwd: str):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] BLOCKED: {command} | Reason: {reason} | Path: {cwd}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to blocked.log: {e}\n")

def check_command(command: str) -> tuple[bool, str]:
    if not command:
        return False, ""
    
    clean_cmd = command.strip()
    
    # 1. rm -rf / rm -fr
    if re.search(r"\brm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b", clean_cmd):
        return True, "Recursive force deletion (rm -rf)"
        
    # 2. DROP TABLE
    if re.search(r"\bDROP\s+TABLE\b", clean_cmd, re.IGNORECASE):
        return True, "SQL destructive command (DROP TABLE)"
        
    # 3. TRUNCATE TABLE
    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", clean_cmd, re.IGNORECASE):
        return True, "SQL table purge (TRUNCATE)"
        
    # 4. git push --force / -f
    if re.search(r"\bgit\s+push\s+.*(?:--force|-f)\b", clean_cmd):
        return True, "Git force push overwriting remote history"
        
    # 5. DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", clean_cmd, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", clean_cmd, re.IGNORECASE):
            return True, "Unbounded SQL deletion without WHERE clause"
            
    return False, ""

def main():
    command = ""
    cwd = os.getcwd()

    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    command = payload.get("tool_input", {}).get("command") or payload.get("command") or raw_input
                    cwd = payload.get("cwd") or os.getcwd()
                except json.JSONDecodeError:
                    command = raw_input.strip()
        except Exception:
            pass

    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, cwd)
        
        error_msg = f"""
🛑 [SECURITY HOOK BLOCKED]
The following destructive command was blocked by pre-tool-use policy:
Command: {command}
Reason:  {reason}
Logged:  ~/.claude/hooks/blocked.log
"""
        sys.stderr.write(error_msg.strip() + "\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
