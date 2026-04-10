#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Blocks destructive bash commands
Bounty: $100 - claude-builders-bounty #3
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    (r'\brm\s+(-[rf]+\s+|.*\s+-[rf]+\s*)', "rm -rf: recursive/force delete"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE: SQL destructive command"),
    (r'\bgit\s+push\s+.*--force', "git push --force: force push"),
    (r'\bTRUNCATE\s+', "TRUNCATE: SQL destructive command"),
    (r'\bDELETE\s+FROM\s+\w+\s*;', "DELETE FROM without WHERE: SQL destructive command"),
    (r'\bDELETE\s+FROM\s+\w+\s*$', "DELETE FROM without WHERE: SQL destructive command"),
]

# Log file path
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

def ensure_log_dir():
    """Ensure log directory exists"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_blocked(command: str, reason: str, project_path: str):
    """Log blocked command to file"""
    ensure_log_dir()
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: '{command}' - Reason: {reason} - Path: {project_path}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if command contains dangerous patterns.
    Returns (is_dangerous, reason)
    """
    command_upper = command.upper()
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    
    return False, ""

def main():
    # Read input from Claude Code
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Allow if we can't parse
    
    # Extract command and project path
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("project_path", os.getcwd())
    
    # Only check bash/exec commands
    if tool_name not in ["bash", "exec"]:
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    # Check for dangerous patterns
    is_dangerous, reason = check_command(command)
    
    if is_dangerous:
        # Log the blocked attempt
        log_blocked(command, reason, project_path)
        
        # Output blocking message for Claude
        block_message = {
            "decision": "reject",
            "message": f"🚫 BLOCKED: Command '{command}' was blocked for safety.\n\nReason: {reason}\n\nThis action has been logged to {LOG_FILE}"
        }
        print(json.dumps(block_message))
        sys.exit(0)
    
    # Allow the command
    sys.exit(0)

if __name__ == "__main__":
    main()
