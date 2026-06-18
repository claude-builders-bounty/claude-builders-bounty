#!/usr/bin/env python3
"""
block.py - PreToolUse Security Hook for Claude Code.

Blocks destructive bash commands:
- rm -rf
- DROP TABLE  
- git push --force
- TRUNCATE
- DELETE FROM without WHERE

Logs blocked attempts to ~/.claude/hooks/blocked.log.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*[rR][fF]|-[a-zA-Z]*[fF][rR]|-[a-zA-Z]*r|-[a-zA-Z]*f)', 'rm -rf'),
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)', 'DROP statement'),
    (r'\bgit\s+push\s+(--force|-f)', 'git force push'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'TRUNCATE statement'),
    (r'\bDELETE\s+FROM\s+\w+\s*;?\s*$', 'DELETE FROM without WHERE'),
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command, rule, project_path):
    """Log blocked attempt."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED | Rule: {rule} | Command: {command} | Project: {project_path}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Failed to log: {e}", file=sys.stderr)


def is_destructive(command):
    """Check if command is destructive."""
    for pattern, rule_name in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return rule_name
    return None


def main():
    """Main hook logic."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("Bash", "ExecuteCommand"):
        sys.exit(0)
    
    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)
    
    rule = is_destructive(command)
    if rule:
        project = input_data.get("cwd", os.getcwd())
        log_blocked(command, rule, project)
        response = {
            "decision": "block",
            "reason": f"Blocked '{rule}': {command}"
        }
        print(json.dumps(response))
        sys.exit(2)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
