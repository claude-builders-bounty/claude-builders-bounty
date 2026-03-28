#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.
Intercepts dangerous commands before execution and logs blocked attempts.

Installation:
  mkdir -p ~/.claude/hooks
  cp block_destructive_commands.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/block_destructive_commands.py
"""

import json
import sys
import os
import re
from datetime import datetime

# Log file location
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Destructive patterns to block
DESTRUCTIVE_PATTERNS = [
    # Filesystem destruction
    (r'rm\s+(-[rf]+\s+)*(-[rf]+\s+)*(/|\*|\.\.|~)', 'rm -rf: Recursive force delete'),
    (r'rm\s+-rf\s+', 'rm -rf: Recursive force delete'),
    (r'rm\s+--no-preserve-root\s+', 'rm --no-preserve-root: System root deletion'),
    
    # Database destruction
    (r'DROP\s+TABLE\s+', 'DROP TABLE: Database table deletion'),
    (r'TRUNCATE\s+(TABLE\s+)?', 'TRUNCATE: Database table truncation'),
    (r'DELETE\s+FROM\s+\w+\s*(;|--|/\*|$)', 'DELETE FROM without WHERE: Full table deletion'),
    
    # Git destruction
    (r'git\s+push\s+--force', 'git push --force: Force push (rewrites history)'),
    (r'git\s+push\s+-f\s+', 'git push -f: Force push (rewrites history)'),
    
    # System destruction
    (r'mkfs\.', 'mkfs: Filesystem format'),
    (r'dd\s+.*of=/dev/', 'dd to /dev: Disk write'),
    (r':\(\)\{\s*:\|\:&\s*\};:', 'Fork bomb'),
    
    # Permission/ownership destruction
    (r'chmod\s+-R\s+777\s+/', 'chmod -R 777 /: System-wide permissions'),
    (r'chown\s+-R\s+', 'chown -R: Recursive ownership change (potential risk)'),
]

def log_blocked(command: str, reason: str, project_path: str):
    """Log blocked command to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED | Reason: {reason} | Command: {command} | Path: {project_path}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any destructive pattern."""
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    """Main hook entry point."""
    # Read input from stdin (Claude Code sends tool use request as JSON)
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No input, allow (nothing to check)
            print(json.dumps({"allow": True}))
            return
        
        request = json.loads(input_data)
    except json.JSONDecodeError:
        # Invalid JSON, allow passthrough
        print(json.dumps({"allow": True}))
        return
    
    # Check if this is a bash command execution
    tool_name = request.get("tool", "")
    params = request.get("params", {})
    
    if tool_name != "bash":
        # Not a bash command, allow
        print(json.dumps({"allow": True}))
        return
    
    # Extract command from params
    command = params.get("command", "")
    if not command:
        command = params.get("c", "")
    
    if not command:
        # No command, allow
        print(json.dumps({"allow": True}))
        return
    
    # Check for destructive patterns
    is_destructive, reason = check_command(command)
    
    if is_destructive:
        # Get project path
        project_path = os.getcwd()
        
        # Log the blocked attempt
        log_blocked(command, reason, project_path)
        
        # Block the command with clear message
        response = {
            "allow": False,
            "reason": f"🚫 BLOCKED: Destructive command detected\n\n"
                     f"Pattern: {reason}\n"
                     f"Command: {command}\n\n"
                     f"This command has been blocked for safety. "
                     f"If you need to run this command intentionally, "
                     f"please do so directly in your terminal.\n\n"
                     f"Logged to: {LOG_FILE}"
        }
        print(json.dumps(response))
    else:
        # Safe command, allow
        print(json.dumps({"allow": True}))

if __name__ == "__main__":
    main()
