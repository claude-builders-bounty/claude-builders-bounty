#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.
Install: cp pre_tool_use.py ~/.claude/hooks/
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
"""

import json
import sys
import re
import os
from datetime import datetime, timezone
from pathlib import Path

# Patterns that are always blocked (no exceptions)
ALWAYS_BLOCK = [
    r'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|\s*-\s*)+.*',  # rm -rf or rm -f
    r'git\s+push\s+.*--force',                         # git push --force
    r'DROP\s+TABLE',                                   # SQL DROP TABLE
    r'TRUNCATE\s+TABLE',                              # SQL TRUNCATE
    r'mkfs\.',                                         # Format filesystem
    r'dd\s+if=.*of=/dev/[sh]d',                        # Disk overwrite
    r'\b>:?/dev/[sh]d[a-z]\d?\b',                     # Redirect to disk
    r'\bshutdown\b',                                   # System shutdown
    r'\breboot\b',                                     # System reboot
    r'\bmv\s+/\s+',                                    # mv root
    r'chmod\s+(-R\s+)?000\s+/\b',                      # chmod 000 root
]

# Patterns that require a WHERE clause to be safe
NEEDS_WHERE = [
    r'DELETE\s+FROM\s+\w+',                            # DELETE FROM table (without WHERE)
]

# Allowed exceptions (fine-tuned)
ALLOWED = [
    r'rm\s+-f\s+.*\.log$',                             # rm -f *.log (safe)
    r'rm\s+-f\s+.*\.tmp$',                             # rm -f *.tmp (safe)
    r'git\s+push\s+--force-with-lease',                # force-with-lease is safer
]

BLOCKED_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command: str, reason: str, project_path: str = None):
    """Log a blocked attempt to the blocked.log file."""
    BLOCKED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "reason": reason,
        "project_path": project_path or os.getcwd()
    }
    with open(BLOCKED_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str, project_path: str = None) -> tuple:
    """
    Check if a command should be blocked.
    Returns (is_blocked: bool, reason: str).
    """
    # Normalize command for matching
    normalized = command.strip().lower()
    
    # Check allowed exceptions first
    for pattern in ALLOWED:
        if re.search(pattern, command, re.IGNORECASE):
            return False, "Allowed by exception rule"
    
    # Check always-block patterns
    for pattern in ALWAYS_BLOCK:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Destructive pattern matched: {pattern}"
    
    # Check patterns that need WHERE
    for pattern in NEEDS_WHERE:
        if re.search(pattern, command, re.IGNORECASE):
            if 'where' not in normalized:
                return True, "DELETE FROM without WHERE clause"
            return False, "DELETE with WHERE — safe"
    
    return False, "No destructive patterns detected"


def main():
    # Claude Code sends JSON on stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If stdin is not JSON (e.g., direct execution), read as text
        data = {"tool_name": "Bash", "tool_input": {"command": sys.stdin.read()}}
    
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    
    # Only intercept Bash tool
    if tool_name != "Bash":
        # Pass through unchanged
        print(json.dumps(data))
        return
    
    command = tool_input.get("command", "")
    project_path = data.get("project_path", os.getcwd())
    
    is_blocked, reason = check_command(command, project_path)
    
    if is_blocked:
        log_blocked(command, reason, project_path)
        
        # Return modified response that blocks execution
        response = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"echo '⛔ BLOCKED: {reason}\nCommand: {command}\nThis destructive command was blocked by the safety hook.\nIf you need to run this, disable the hook temporarily: mv ~/.claude/hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py.disabled'",
                "description": "Blocked destructive command"
            },
            "project_path": project_path,
            "_hook_blocked": True,
            "_hook_reason": reason
        }
        
        # Also print to stderr so Claude sees the block in real-time
        print(f"\n🔒 [SAFETY HOOK] Blocked destructive command:\n   {command}\n   Reason: {reason}\n", file=sys.stderr)
        
        print(json.dumps(response))
    else:
        # Pass through unchanged
        print(json.dumps(data))


if __name__ == "__main__":
    main()
