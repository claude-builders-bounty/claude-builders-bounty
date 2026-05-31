#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.
Intercepts dangerous patterns before execution.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

DANGEROUS_PATTERNS = [
    (r'\brm\s+(-[rfRF]+\s+)*/', "rm -rf on root or absolute paths"),
    (r'\brm\s+-[rfRF]*\s+\*', "rm with wildcard"),
    (r'\brm\s+-rf\b', "rm -rf command"),
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', "DROP TABLE/DATABASE"),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', "TRUNCATE TABLE"),
    (r'\bDELETE\s+FROM\s+\w+\s*$', "DELETE without WHERE clause"),
    (r'\bDELETE\s+FROM\s+\w+\s*;', "DELETE without WHERE clause"),
    (r'\bgit\s+push\s+(-f|--force)', "git push --force"),
    (r'\bgit\s+push\s+\S+\s+\S+\s+(-f|--force)', "git push --force"),
    (r'\bgit\s+reset\s+--hard', "git reset --hard"),
    (r':\s*>\s*/', "Overwriting files with redirection"),
    (r'\bdd\s+.*of=/', "dd writing to disk"),
    (r'\bmkfs\.', "Formatting filesystem"),
    (r'\bchmod\s+-R\s+777\s+/', "chmod 777 on root"),
    (r'\bchown\s+-R\s+.*\s+/', "chown on root"),
]

def get_log_path():
    """Get the path to the blocked commands log file."""
    claude_dir = Path.home() / ".claude" / "hooks"
    claude_dir.mkdir(parents=True, exist_ok=True)
    return claude_dir / "blocked.log"

def log_blocked_command(command: str, reason: str, project_path: str):
    """Log a blocked command to the log file."""
    log_path = get_log_path()
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n\n"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any dangerous patterns.
    Returns (is_dangerous, reason).
    """
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name not in ("bash", "shell", "execute", "run_command", "Bash"):
        print(json.dumps({"decision": "approve"}))
        return
    
    command = tool_input.get("command", "") or tool_input.get("cmd", "") or tool_input.get("script", "")
    
    if not command:
        print(json.dumps({"decision": "approve"}))
        return
    
    is_dangerous, reason = check_command(command)
    
    if is_dangerous:
        project_path = input_data.get("cwd", os.getcwd())
        log_blocked_command(command, reason, project_path)
        
        result = {
            "decision": "block",
            "message": f"Command blocked for safety: {reason}. This command pattern can cause irreversible damage. If you need to perform this operation, please ask the user to run it manually."
        }
        print(json.dumps(result))
    else:
        print(json.dumps({"decision": "approve"}))

if __name__ == "__main__":
    main()
