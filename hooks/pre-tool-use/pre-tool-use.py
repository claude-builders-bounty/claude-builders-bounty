#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Block destructive bash commands.
Install: cp pre-tool-use.py ~/.claude/hooks/ (Claude Code auto-discovers hooks in ~/.claude/hooks/)
"""

import json
import re
import os
import sys
from datetime import datetime

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
BLOCKED_LOG = os.path.join(HOOKS_DIR, "blocked.log")

# Patterns that are ALWAYS dangerous, no WHERE safety net
DESTRUCTIVE_PATTERNS = [
    (r'rm\s+-rf\s+[/a-zA-Z0-9_.-]+', "Recursive force delete — destroys data permanently"),
    (r'rm\s+-rf\s+\*', "Recursive force delete of all files — destroys project"),
    (r'DROP\s+TABLE', "SQL DROP TABLE — removes entire table from database"),
    (r'TRUNCATE\s+', "SQL TRUNCATE — removes all rows from table"),
    (r'git\s+push\s+--force', "Force push — overwrites remote history, can lose commits"),
    (r'git\s+push\s+-f', "Force push shorthand — same danger as --force"),
    (r'>\s*/dev/sd[a-z]', "Writing directly to block device — can destroy filesystem"),
]

# Pattern: DELETE FROM without WHERE (only dangerous on data)
DELETE_NO_WHERE = r'DELETE\s+FROM\s+(\w+)(?!\s+WHERE)'

def get_project_path():
    """Try to determine the current project directory."""
    cwd = os.getcwd()
    # Walk up to find a git repo root or package.json or similar marker
    dir = cwd
    for _ in range(10):
        if os.path.exists(os.path.join(dir, '.git')):
            return dir
        parent = os.path.dirname(dir.rstrip('/'))
        if parent == dir:
            break
        dir = parent
    return cwd

def check_command(command: str):
    """Check if command matches any destructive pattern. Returns (blocked, reason)."""
    cmd = command.strip()
    
    # Check fixed patterns
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, reason
    
    # Check DELETE without WHERE
    if re.search(DELETE_NO_WHERE, cmd, re.IGNORECASE):
        # Make sure it's not something like "DELETE FROM ... WHERE ..."
        # The negative lookahead should handle this, but let's be extra sure
        if not re.search(r'DELETE\s+FROM\s+\w+\s+WHERE', cmd, re.IGNORECASE):
            return True, "DELETE FROM without WHERE clause — removes ALL rows"
    
    return False, None

def log_blocked(command: str, reason: str, project_path: str):
    """Append blocked attempt to the log file."""
    os.makedirs(HOOKS_DIR, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED | project: {project_path} | reason: {reason} | cmd: {command}\n"
    with open(BLOCKED_LOG, "a") as f:
        f.write(log_entry)

def main():
    try:
        # Claude Code passes hook payload via stdin
        payload = json.loads(sys.stdin.read())
        
        # Extract command from the hook payload
        # The payload structure: { "tool_name": "...", "tool_input": {...}, ... }
        tool_name = payload.get("tool_name", "")
        
        # For bash tool, the command is in tool_input.command or tool_input (as positional)
        tool_input = payload.get("tool_input", {})
        
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if isinstance(tool_input, list):
                command = str(tool_input[0]) if tool_input else ""
        else:
            # Not a bash command, allow it
            print(json.dumps({"continue": True}))
            return
        
        blocked, reason = check_command(command)
        
        if blocked:
            project = get_project_path()
            log_blocked(command, reason, project)
            
            # Return block response with explanation
            result = {
                "continue": False,
                "reason": f"⛔ HOOK BLOCKED: {reason}\n\nThe command you tried to run has been blocked by the pre-tool-use safety hook.\nReason: {reason}\n\nIf you absolutely need to run this command, you can:\n1. Remove the hook temporarily: rm ~/.claude/hooks/pre-tool-use.py\n2. Or ask the user to approve it explicitly\n\nThis incident has been logged to ~/.claude/hooks/blocked.log"
            }
            print(json.dumps(result))
        else:
            print(json.dumps({"continue": True}))
            
    except json.JSONDecodeError:
        # Not JSON input, allow through
        print(json.dumps({"continue": True}))
    except Exception as e:
        # On error, be permissive (don't break workflows)
        print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
