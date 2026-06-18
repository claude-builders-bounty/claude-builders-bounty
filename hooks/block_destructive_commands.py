#!/usr/bin/env python3
"""
block_destructive_commands.py - PreToolUse hook that blocks destructive bash commands.

This hook intercepts Bash/ExecuteCommand tool calls and blocks dangerous patterns:
- rm -rf (recursive forced deletion)
- DROP TABLE (SQL table destruction)
- git push --force (force push overwrites history)
- TRUNCATE (SQL data destruction)
- DELETE FROM without a WHERE clause (unconditional deletion)

Blocked attempts are logged to ~/.claude/hooks/blocked.log with timestamp,
attempted command, project path, and matched rule.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Regex patterns for destructive commands
BLOCKED_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*[rR][fF]|-[a-zA-Z]*[fF][rR]|-[a-zA-Z]*r|-[a-zA-Z]*f)\b', 'rm -rf recursive delete'),
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'SQL DROP statement'),
    (r'\bgit\s+push\s+(--force|-f)\b', 'git force push'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'SQL TRUNCATE statement'),
    (r'\bDELETE\s+FROM\s+\w+\s*;?\s*$', 'DELETE FROM without WHERE'),
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command, rule, project_path):
    """Log blocked attempt to log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED | Rule: {rule} | Command: {command} | Project: {project_path}\n"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Failed to write to log: {e}", file=sys.stderr)


def is_destructive(command):
    """Check if a command matches any blocked pattern."""
    for pattern, rule_name in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return rule_name
    return None


def main():
    """Read hook input from stdin, check command, output decision."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # If we can't parse, allow (don't block legitimate work)
        print(f"Hook input parse error: {e}", file=sys.stderr)
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "")
    
    # Only check Bash/ExecuteCommand tools
    if tool_name not in ("Bash", "ExecuteCommand", "bash", "execute_command"):
        sys.exit(0)
    
    # Extract command from tool input
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "") or tool_input.get("cmd", "")
    
    if not command:
        sys.exit(0)
    
    # Check for destructive patterns
    matched_rule = is_destructive(command)
    
    if matched_rule:
        project_path = input_data.get("cwd", os.getcwd())
        log_blocked(command, matched_rule, project_path)
        
        # Output denial reason
        response = {
            "decision": "block",
            "reason": f"⛔ Blocked destructive command: '{command}' matched rule '{matched_rule}'"
        }
        print(json.dumps(response))
        sys.exit(2)  # Exit code 2 = blocking error in Claude Code hooks
    
    # Allow command
    sys.exit(0)


if __name__ == "__main__":
    main()
