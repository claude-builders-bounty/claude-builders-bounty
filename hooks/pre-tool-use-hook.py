#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code.
Blocks dangerous bash commands before execution.
Installed at ~/.claude/hooks/pre-tool-use/

Features:
- Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
- Logs every blocked attempt with timestamp, command, project path
- Clear block message explaining why
- Non-interfering with normal commands
"""

import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf (destructive deletion)
    (r'\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\b', 
     "⚠️ BLOCKED: Recursive force deletion (`rm -rf`). Use `rm -r` with confirmation instead."),
    
    # DROP TABLE in SQL
    (r'\bDROP\s+TABLE\b', 
     "⚠️ BLOCKED: `DROP TABLE` detected. Use `DROP TABLE IF EXISTS` in a migration file only."),
    
    # git push --force
    (r'\bgit\s+push\s+(--force|\-f)\b',
     "⚠️ BLOCKED: `git push --force`. Use `git push --force-with-lease` instead."),
    
    # TRUNCATE
    (r'\bTRUNCATE\b', 
     "⚠️ BLOCKED: `TRUNCATE` detected. Use `DELETE` with a WHERE clause."),
    
    # DELETE FROM without WHERE
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',
     "⚠️ BLOCKED: `DELETE FROM` without a WHERE clause. Add a WHERE clause to specify which rows to delete."),
    
    # Dangerous shell operations
    (r'\bmv\s+/[/a-zA-Z]+\s+/dev/null\b',
     "⚠️ BLOCKED: Moving files to /dev/null (data destruction). Use a temporary directory instead."),
    
    # chmod -R 777
    (r'\bchmod\s+-R\s+777\b',
     "⚠️ BLOCKED: `chmod -R 777`. Use more restrictive permissions (e.g., 755 for directories, 644 for files)."),
    
    # dd if=/dev/urandom (destructive)
    (r'\bdd\s+if=/dev/urandom\b',
     "⚠️ BLOCKED: Overwriting with random data. This appears destructive."),
]

def get_project_path():
    """Get the current project path from environment or cwd."""
    return os.environ.get('CLAUDE_PROJECT_PATH', os.getcwd())

def log_blocked(command, pattern_name):
    """Log blocked command to blocked.log."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    project = get_project_path()
    log_entry = f"[{timestamp}] BLOCKED: {command} | Pattern: {pattern_name} | Project: {project}\n"
    
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception:
        pass  # Silently fail if we can't write to log

def check_command(command):
    """Check if a command should be blocked. Returns (blocked: bool, message: str)."""
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, pattern.pattern)
            return True, message
    return False, ""

def main():
    """
    Claude Code hook entry point.
    Reads the tool-use JSON from stdin, checks the command, and either
    passes it through or blocks with an error message.
    """
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not a JSON input — let it pass through
        print(json.dumps({"action": "allow"}))
        return

    # Extract the command from various possible formats
    command = ""
    
    # Format 1: {"command": "..."} 
    if isinstance(input_data, dict):
        if "command" in input_data:
            command = input_data["command"]
        # Format 2: {"tool_use": {"name": "bash", "input": {"command": "..."}}}
        elif "tool_use" in input_data:
            tool_use = input_data["tool_use"]
            if isinstance(tool_use, dict):
                if tool_use.get("name") == "bash":
                    cmd_input = tool_use.get("input", {})
                    if isinstance(cmd_input, dict):
                        command = cmd_input.get("command", "")
        # Format 3: raw bash tool format
        elif "name" in input_data and input_data.get("name") == "bash":
            command = input_data.get("input", {}).get("command", "")
    
    if not command:
        # No command found — allow
        print(json.dumps({"action": "allow"}))
        return
    
    blocked, message = check_command(command)
    
    if blocked:
        print(json.dumps({
            "action": "block",
            "message": message
        }))
    else:
        print(json.dumps({"action": "allow"}))

if __name__ == "__main__":
    main()
