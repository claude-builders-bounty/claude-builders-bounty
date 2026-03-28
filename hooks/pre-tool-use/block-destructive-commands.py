#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.

This hook intercepts bash command executions and blocks potentially dangerous
operations like:
- rm -rf (recursive force delete)
- DROP TABLE (SQL)
- git push --force (force push)
- TRUNCATE (SQL)
- DELETE FROM without WHERE clause (SQL)

Author: HuiNeng6
License: MIT
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Configuration
HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf patterns
    {
        "pattern": r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)*(-[a-zA-Z]*f[a-zA-Z]*\s+)*.*-rf\b|\brm\s+-fr\b|\brm\s+--recursive\s+--force\b",
        "name": "rm -rf",
        "description": "Recursive force delete can destroy entire directory trees"
    },
    # DROP TABLE
    {
        "pattern": r"\bDROP\s+TABLE\b",
        "name": "DROP TABLE",
        "description": "DROP TABLE will permanently delete database tables"
    },
    # git push --force
    {
        "pattern": r"\bgit\s+push\s+.*(--force|-f)\b",
        "name": "git push --force",
        "description": "Force push can overwrite remote history and cause data loss"
    },
    # TRUNCATE
    {
        "pattern": r"\bTRUNCATE\s+TABLE\b|\bTRUNCATE\s+(?!TABLE)[A-Za-z_]",
        "name": "TRUNCATE",
        "description": "TRUNCATE removes all rows from a table without logging"
    },
    # DELETE FROM without WHERE
    {
        "pattern": r"\bDELETE\s+FROM\s+\S+\s*;",
        "name": "DELETE FROM without WHERE",
        "description": "DELETE without WHERE will remove all rows from the table"
    },
    # Additional dangerous patterns
    {
        "pattern": r"\bDELETE\s+FROM\s+\S+\s*$",
        "name": "DELETE FROM without WHERE",
        "description": "DELETE without WHERE will remove all rows from the table"
    },
]


def log_blocked_command(command: str, pattern_name: str, pattern_desc: str, project_path: str = "") -> None:
    """Log a blocked command to the blocked.log file."""
    # Ensure hooks directory exists
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"""
{'='*60}
[{timestamp}] BLOCKED COMMAND
Pattern: {pattern_name}
Description: {pattern_desc}
Project Path: {project_path or 'Unknown'}
Attempted Command:
{command}
{'='*60}
"""
    
    with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry)


def check_command_safety(command: str) -> tuple[bool, str, str]:
    """
    Check if a command contains dangerous patterns.
    
    Returns:
        tuple: (is_safe, pattern_name, pattern_description)
    """
    # Normalize command for checking
    normalized_cmd = command.strip()
    
    for danger in DANGEROUS_PATTERNS:
        if re.search(danger["pattern"], normalized_cmd, re.IGNORECASE):
            return False, danger["name"], danger["description"]
    
    return True, "", ""


def main():
    """Main hook function."""
    # Read the tool use request from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # If we can't parse input, allow the operation (fail open)
        print(json.dumps({"action": "allow"}))
        sys.exit(0)
    
    # Extract tool information
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("project_path", "")
    
    # We only intercept bash/exec commands
    if tool_name not in ("bash", "exec"):
        print(json.dumps({"action": "allow"}))
        sys.exit(0)
    
    # Get the command to check
    command = tool_input.get("command", "") or tool_input.get("bash_command", "")
    
    if not command:
        print(json.dumps({"action": "allow"}))
        sys.exit(0)
    
    # Check command safety
    is_safe, pattern_name, pattern_desc = check_command_safety(command)
    
    if not is_safe:
        # Log the blocked command
        log_blocked_command(command, pattern_name, pattern_desc, project_path)
        
        # Return block response with explanation
        response = {
            "action": "block",
            "message": f"""
⚠️  DESTRUCTIVE COMMAND BLOCKED

The command you attempted to execute has been blocked for safety:

**Pattern detected:** {pattern_name}
**Reason:** {pattern_desc}

**Attempted command:**
```
{command}
```

If you're sure you want to proceed with this potentially destructive operation:
1. Verify you understand the consequences
2. Use a safer alternative if possible
3. Manually execute the command if absolutely necessary

This attempt has been logged to: {BLOCKED_LOG}
""".strip()
        }
        print(json.dumps(response))
        sys.exit(0)
    
    # Command is safe, allow it
    print(json.dumps({"action": "allow"}))
    sys.exit(0)


if __name__ == "__main__":
    main()