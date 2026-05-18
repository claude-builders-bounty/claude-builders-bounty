#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook
Blocks destructive bash commands before execution.
Install: ln -sf $(pwd)/hooks/pre_tool_use.py ~/.claude/hooks/pre-tool-use/
"""

import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path

# === Configuration ===
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
DANGEROUS_PATTERNS = [
    # File destruction
    (r'\brm\s+(-[rf]+|[rf]+)\s+/?(bin|boot|dev|etc|home|lib|mnt|opt|proc|root|run|sbin|srv|sys|tmp|usr|var)\b', 
     "Dangerous recursive deletion of system directory blocked"),
    (r'\brm\s+(-[rf]+|[rf]+)\s+/?\*\s*$', 
     "Wildcard recursive deletion blocked (potential system-wide impact)"),
    (r'\brm\s+(-[rf]+|[rf]+)\s+\.', 
     "Hidden file/directory recursive deletion blocked"),
    (r'\brm\s+(-[rf]+|[rf]+)\s+/', 
     "Root filesystem deletion attempt blocked"),
    
    # Dangerous git commands
    (r'\bgit\s+push\s+--force\b', 
     "Force push blocked — use 'git push --force-with-lease' instead"),
    (r'\bgit\s+push\s+-f\b', 
     "Force push blocked — use 'git push --force-with-lease' instead"),
    
    # Database destruction
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 
     "DROP statement blocked — destructive database operation"),
    (r'\bTRUNCATE\s+\w+', 
     "TRUNCATE blocked — destructive table operation"),
    (r'\bDELETE\s+FROM\s+\w+(?:\s+(?!WHERE\b))', 
     "Unqualified DELETE blocked — requires WHERE clause"),
    
    # System operations
    (r'\b(mkfs|fdisk|dd|format)\s+', 
     "Filesystem/disk operation blocked"),
    (r'\bchmod\s+-?R?\s*777\b', 
     "Overly permissive chmod blocked"),
    (r'\b(?:shutdown|reboot|init\s+6|halt)\b', 
     "System shutdown/reboot blocked"),
    
    # Encryption/ransomware
    (r'\bmv\s+.*\s+(\.encrypted|\.locked|\.crypt)\s*$',
     "Suspicious file rename pattern blocked"),
]

def check_command(command: str) -> tuple:
    """Check if command matches any dangerous pattern."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def log_blocked(command: str, reason: str) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log."""
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_path = os.getcwd()
    
    log_entry = (
        f"[{timestamp}]\n"
        f"  Command: {command}\n"
        f"  Reason:  {reason}\n"
        f"  Project: {project_path}\n"
        f"{'─' * 60}\n"
    )
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def main():
    """Main hook entry point."""
    # Read the tool use JSON from stdin
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            # No input means no tool invocation, allow
            sys.exit(0)
        
        tool_use = json.loads(raw_input)
    except json.JSONDecodeError:
        # Not JSON input, allow
        sys.exit(0)
    
    # Extract the command from the tool use
    command = ""
    if isinstance(tool_use, dict):
        # Check various possible locations for the command
        command = (tool_use.get("command") or 
                   tool_use.get("input", {}).get("command") or
                   tool_use.get("bash", "") or
                   tool_use.get("args", {}).get("command", ""))
    
    if not command:
        sys.exit(0)
    
    # Check for dangerous patterns
    is_dangerous, reason = check_command(command)
    
    if is_dangerous:
        log_blocked(command, reason)
        error_msg = (
            f"⛔ BLOCKED: {reason}\n\n"
            f"Command: {command}\n"
            f"Logged to: {LOG_FILE}\n\n"
            f"💡 Tip: If you need to run this, use the project's "
            f"deployment script or CI/CD pipeline instead."
        )
        print(json.dumps({"error": error_msg, "blocked": True}))
        sys.exit(1)
    
    # Command is safe, allow execution
    sys.exit(0)

if __name__ == "__main__":
    main()
