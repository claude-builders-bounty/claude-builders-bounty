#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands."""
import sys
import json
import os
import re
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    r'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)*-[a-zA-Z]*r[a-zA-Z]*',  # rm -rf variants
    r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)*-[a-zA-Z]*f[a-zA-Z]*',  # rm -fr variants
    r'DROP\s+TABLE',
    r'TRUNCATE\s+(TABLE\s+)?',
    r'DELETE\s+FROM\s+\S+(\s+WHERE\s+.*)?$',  # DELETE without WHERE or with empty WHERE
    r'git\s+push\s+(-[a-zA-Z]*-force[a-zA-Z]*|--force)',
    r'git\s+push\s+-f',
    r'mkfs\.',
    r'dd\s+if=.*of=/dev/',
    r'>\s*/dev/sd[a-z]',
    r'chmod\s+(-R\s+)?777\s+/',
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command: str, project_path: str, reason: str):
    """Log blocked command to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] BLOCKED | project={project_path} | reason={reason} | command={command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked pattern. Returns (is_blocked, reason)."""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Matches dangerous pattern: {pattern}"
    
    # Special check: DELETE FROM without proper WHERE clause
    delete_match = re.search(r'DELETE\s+FROM\s+(\S+)(.*)', command, re.IGNORECASE)
    if delete_match:
        where_clause = delete_match.group(2).strip()
        if not where_clause or not re.search(r'WHERE', where_clause, re.IGNORECASE):
            return True, "DELETE FROM without WHERE clause"
        # Check for trivially true WHERE
        if re.search(r'WHERE\s+1\s*=\s*1', where_clause, re.IGNORECASE):
            return True, "DELETE FROM with trivially true WHERE (1=1)"
    
    return False, ""

def main():
    """Main hook entry point."""
    try:
        # Read input from stdin (Claude Code passes JSON)
        input_data = json.loads(sys.stdin.read())
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        project_path = input_data.get("project_path", os.getcwd())
        
        # Only intercept bash/shell commands
        if tool_name not in ("bash", "shell", "exec", "run_command"):
            print(json.dumps({"decision": "allow"}))
            return
        
        command = tool_input.get("command", "") or tool_input.get("cmd", "")
        if not command:
            print(json.dumps({"decision": "allow"}))
            return
        
        is_blocked, reason = check_command(command)
        
        if is_blocked:
            log_blocked(command, project_path, reason)
            message = (
                f"⛔ BLOCKED: This command was prevented by safety hook.\n"
                f"Reason: {reason}\n"
                f"Command: {command[:200]}\n\n"
                f"If this is intentional, run the command manually outside Claude Code."
            )
            print(json.dumps({
                "decision": "block",
                "message": message
            }))
        else:
            print(json.dumps({"decision": "allow"}))
    
    except Exception as e:
        # On error, allow but log
        print(json.dumps({"decision": "allow", "warning": str(e)}))

if __name__ == "__main__":
    main()
