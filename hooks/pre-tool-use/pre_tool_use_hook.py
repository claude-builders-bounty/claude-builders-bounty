#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

This hook intercepts bash commands before execution and blocks potentially
dangerous operations like rm -rf, DROP TABLE, force pushes, etc.

Installation:
    mkdir -p ~/.claude/hooks
    cp pre_tool_use_hook.py ~/.claude/hooks/

Hook format: Receives JSON from stdin, outputs JSON to stdout
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path


# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    # File system destruction
    (r'rm\s+(-[rf]+\s+|--recursive\s+|--force\s+).*\S', 
     "'rm -rf' can cause irreversible data loss. Use 'rm -r' (without -f) or 'rmdir' for safer deletion."),
    
    # SQL destructive operations
    (r'DROP\s+(TABLE|DATABASE|SCHEMA)', 
     "SQL DROP statements can destroy data. Please verify before running."),
    
    (r'TRUNCATE\s+(TABLE\s+)?\w+', 
     "TRUNCATE removes all data from a table. Please verify before running."),
    
    (r'DELETE\s+FROM\s+\w+\s*;?\s*$', 
     "DELETE without WHERE clause removes all rows. Add a WHERE clause."),
    
    (r'DELETE\s+FROM\s+\w+\s*;?\s*(?!WHERE)', 
     "DELETE without WHERE clause removes all rows. Add a WHERE clause."),
    
    # Git destructive operations
    (r'git\s+push\s+.*(-f|--force)', 
     "Force push can destroy remote history. Use regular push or --force-with-lease."),
    
    (r'git\s+push\s+.*--force-with-lease.*--force', 
     "Multiple force flags detected. Please verify your intent."),
    
    # Fork bomb
    (r':\(\)\s*\{\s*:\|:&\s*\}\s*;', 
     "Fork bomb detected. This can crash your system."),
    
    # Disk operations
    (r'dd\s+.*of=/dev/', 
     "Direct disk writing can corrupt data. Please verify target device."),
    
    (r'mkfs\s+', 
     "Formatting a filesystem will erase all data. Please verify."),
    
    # Network destruction
    (r'iptables\s+.*-F', 
     "Flushing iptables can remove firewall rules. Please verify."),
    
    # Permission changes
    (r'chmod\s+(-R\s+)?777', 
     "chmod 777 makes files world-writable. This is a security risk."),
    
    # System halt
    (r'(shutdown|reboot|halt|poweroff)(\s|$)', 
     "System shutdown/reboot commands. Please verify."),
]


def log_blocked_command(command: str, reason: str, project_path: str):
    """Log blocked command to file."""
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] BLOCKED: \"{command}\" in {project_path}\n"
    log_entry += f"  Reason: {reason}\n\n"
    
    with open(log_file, "a") as f:
        f.write(log_entry)


def check_command_safety(command: str) -> tuple[bool, str]:
    """
    Check if a command is safe to execute.
    
    Returns:
        tuple: (is_safe: bool, reason: str)
    """
    # Normalize command for matching
    normalized = command.strip()
    upper_normalized = normalized.upper()
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, reason
        
        # Also check uppercase version for SQL commands
        if re.search(pattern, upper_normalized, re.IGNORECASE):
            return False, reason
    
    return True, ""


def main():
    """Main hook function."""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        
        # Parse JSON input
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            # If not valid JSON, pass through
            print(json.dumps({"action": "allow"}))
            return
        
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        
        # Only check bash commands
        if tool_name != "bash":
            print(json.dumps({"action": "allow"}))
            return
        
        command = tool_input.get("command", "")
        if not command:
            print(json.dumps({"action": "allow"}))
            return
        
        # Get current working directory for logging
        project_path = os.getcwd()
        
        # Check command safety
        is_safe, reason = check_command_safety(command)
        
        if not is_safe:
            # Log the blocked command
            log_blocked_command(command, reason, project_path)
            
            # Return block response with clear message
            response = {
                "action": "block",
                "message": f"""🚫 BLOCKED: Potentially destructive command detected

Command: {command}

Reason: {reason}

This attempt has been logged to ~/.claude/hooks/blocked.log

If you're sure you want to run this command, you can:
1. Modify the command to be safer
2. Ask the user to run it manually
3. Request explicit confirmation"""
            }
            print(json.dumps(response))
        else:
            # Allow safe commands
            print(json.dumps({"action": "allow"}))
            
    except Exception as e:
        # On error, allow the command but log the error
        error_log = Path.home() / ".claude" / "hooks" / "hook_errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        
        with open(error_log, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] Hook error: {e}\n")
        
        # Allow command on error (fail-open for safety)
        print(json.dumps({"action": "allow"}))


if __name__ == "__main__":
    main()