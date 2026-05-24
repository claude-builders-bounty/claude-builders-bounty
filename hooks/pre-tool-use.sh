#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook — Dangerous Command Blocker
Blocks destructive bash commands before they execute.
Author: OEN (for claude-builders-bounty $100)
"""

import json
import sys
import os
from datetime import datetime

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    "rm -rf",
    "rm -Rf",
    "rm -fr",
    "rm -FR",
    "DROP TABLE",
    "DROP DATABASE",
    "git push --force",
    "git push -f",
    "TRUNCATE",
    "DELETE FROM",
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command: str, reason: str):
    """Log blocked attempt with timestamp and details."""
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()
    
    log_entry = f"[{timestamp}] BLOCKED | Reason: {reason} | Command: {command} | Path: {project_path}\n"
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if command matches dangerous patterns.
    Returns (is_dangerous, reason)
    """
    cmd_upper = command.upper()
    
    # Check rm -rf variants
    if "RM " in cmd_upper and ("-RF" in cmd_upper or "-FR" in cmd_upper or "-R -F" in cmd_upper):
        return True, "Destructive file deletion (rm -rf)"
    
    # Check SQL injection patterns
    if "DROP TABLE" in cmd_upper or "DROP DATABASE" in cmd_upper:
        return True, "Destructive SQL operation (DROP)"
    
    if "TRUNCATE" in cmd_upper:
        return True, "Destructive SQL operation (TRUNCATE)"
    
    # Check DELETE FROM without WHERE
    if "DELETE FROM" in cmd_upper:
        if "WHERE" not in cmd_upper:
            return True, "SQL DELETE without WHERE clause (dangerous!)"
    
    # Check force git push
    if "GIT PUSH" in cmd_upper and ("--FORCE" in cmd_upper or " -F " in cmd_upper or " -F\n" in cmd_upper):
        return True, "Force git push (can overwrite remote history)"
    
    return False, ""

def main():
    # Read input from stdin (Claude Code sends JSON with tool info)
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No input, allow through
            sys.exit(0)
        
        # Parse the hook input
        hook_input = json.loads(input_data)
        
        # Extract command if this is a bash/tool call
        # Claude Code hook format varies, check for command in different places
        command = None
        
        if "tool" in hook_input:
            tool = hook_input.get("tool", {})
            if isinstance(tool, dict):
                command = tool.get("command") or tool.get("content") or tool.get("input")
        
        if not command:
            # Try direct command field
            command = hook_input.get("command") or hook_input.get("content")
        
        if not command:
            # No command found, allow through
            sys.exit(0)
        
        # Convert to string if needed
        command_str = str(command)
        
        # Check if dangerous
        is_dangerous, reason = check_command(command_str)
        
        if is_dangerous:
            # Log the blocked attempt
            log_blocked(command_str, reason)
            
            # Output rejection message (Claude Code will display this)
            rejection = {
                "reject": True,
                "reason": f"🚫 BLOCKED: {reason}\n\n"
                         f"The command '{command_str[:100]}...' has been blocked for safety.\n\n"
                         f"If you believe this is a mistake, review the command carefully.\n"
                         f"Logged to: {LOG_FILE}"
            }
            print(json.dumps(rejection))
            sys.exit(1)
        
        # Command is safe, allow through
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Invalid JSON, allow through (might be plain text)
        sys.exit(0)
    except Exception as e:
        # On error, allow through but log
        sys.exit(0)

if __name__ == "__main__":
    main()
