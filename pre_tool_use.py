#!/usr/bin/env python3
"""
Claude Code pre-tool-use safety hook.
Blocks dangerous bash commands before execution.

Installation:
  mkdir -p ~/.claude/hooks/
  cp pre_tool_use.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre_tool_use.py
"""
import sys
import json
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', 'Recursive force delete (rm -rf)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE statement'),
    (r'\bgit\s+push\s+.*--force\b', 'Force push to remote'),
    (r'\bgit\s+push\s+.*-f\b', 'Force push to remote (-f)'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'TRUNCATE table'),
    (r'\bDELETE\s+FROM\s+\w+\s*$', 'DELETE FROM without WHERE clause'),
    (r'\bDELETE\s+FROM\s+\w+(?!.*\bWHERE\b)', 'DELETE FROM without WHERE clause'),
    (r'\bshutdown\b', 'System shutdown command'),
    (r'\breboot\b', 'System reboot command'),
    (r'\bchmod\s+777\b', 'World-writable permissions (chmod 777)'),
    (r'\b>:?\s*/dev/sd[a-z]', 'Writing directly to block device'),
    (r'\bmkfs\.', 'Filesystem format command'),
    (r'\bdd\s+if=', 'Raw disk copy (dd) — potentially destructive'),
    (r'\bfork\s+bomb', 'Fork bomb pattern'),
    (r':\(\)\s*\{', 'Fork bomb bash function'),
]

def log_block(command: str, reason: str, project_path: str):
    """Log blocked attempt to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Reason:   {reason}\n"
        f"  Command:  {command}\n"
        f"  Project:  {project_path}\n"
        f"  {'-' * 40}\n"
    )
    with open(LOG_FILE, 'a') as f:
        f.write(entry)


def check_command(command: str, project_path: str) -> dict | None:
    """Check if a command matches any blocked patterns. Returns block info or None."""
    import re
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "blocked": True,
                "pattern": pattern,
                "reason": reason,
                "command": command,
            }
    
    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("cwd", os.getcwd())
    
    # Only check bash/shell commands
    if tool_name not in ("bash", "shell", "terminal", "execute_command"):
        print(json.dumps({"continue": True}))
        return
    
    # Extract command
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
    
    if not command:
        print(json.dumps({"continue": True}))
        return
    
    # Check against blocked patterns
    result = check_command(command, project_path)
    
    if result:
        log_block(command, result["reason"], project_path)
        
        print(json.dumps({
            "continue": False,
            "reason": (
                f"⚠️  BLOCKED: {result['reason']}\n\n"
                f"The command was:\n  {command}\n\n"
                f"This command matches a dangerous pattern and was blocked "
                f"for safety. Blocked attempts are logged to: {LOG_FILE}\n\n"
                f"If you are sure this is intentional, please:\n"
                f"  1. Review the command carefully\n"
                f"  2. Run it manually in your terminal\n"
                f"  3. Or temporarily disable this hook"
            )
        }))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
