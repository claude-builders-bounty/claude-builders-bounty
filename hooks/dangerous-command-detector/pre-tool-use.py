#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Dangerous Command Detector

Blocks dangerous bash commands before execution to prevent accidental damage.

Installation:
  mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre-tool-use.py

Configuration: Add to ~/.claude/config.json:
  {
    "hooks": {
      "pre_tool_use": ["~/.claude/hooks/pre-tool-use.py"]
    }
  }
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    {
        "pattern": r"\brm\s+(-[rf]+\s+|-[a-z]*r[a-z]*\s+|-[a-z]*f[a-z]*\s+).*",
        "name": "rm -rf",
        "description": "Recursive force delete can cause irreversible data loss",
        "severity": "critical"
    },
    {
        "pattern": r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
        "name": "DROP TABLE/DATABASE",
        "description": "Dropping tables or databases causes permanent data loss",
        "severity": "critical"
    },
    {
        "pattern": r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z_]",
        "name": "TRUNCATE",
        "description": "Truncating tables removes all data without rollback",
        "severity": "critical"
    },
    {
        "pattern": r"\bgit\s+push\s+.*--force\b",
        "name": "git push --force",
        "description": "Force pushing can overwrite remote history and cause data loss",
        "severity": "critical"
    },
    {
        "pattern": r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)",
        "name": "DELETE FROM without WHERE",
        "description": "Deleting without WHERE clause removes all rows",
        "severity": "critical"
    },
    {
        "pattern": r">\s*/dev/(sd[a-z]|hd[a-z]|nvme[0-9])",
        "name": "Direct disk write",
        "description": "Writing directly to disk devices can corrupt filesystems",
        "severity": "critical"
    },
    {
        "pattern": r"\bchmod\s+(-R\s+)?777\b",
        "name": "chmod 777",
        "description": "World-writable permissions are a security risk",
        "severity": "high"
    },
    {
        "pattern": r"\bcurl\s+.*\|\s*(sudo\s+)?bash\b",
        "name": "curl | bash",
        "description": "Piping remote content to bash is a security risk",
        "severity": "high"
    },
    {
        "pattern": r"\bwget\s+.*\|\s*(sudo\s+)?bash\b",
        "name": "wget | bash",
        "description": "Piping remote content to bash is a security risk",
        "severity": "high"
    },
    {
        "pattern": r"\bdd\s+.*of=/dev/(sd[a-z]|hd[a-z]|nvme[0-9])",
        "name": "dd to disk",
        "description": "dd to disk devices can destroy data",
        "severity": "critical"
    }
]

# Log file path
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_command(command: str, pattern_name: str, description: str, project_path: str = ""):
    """Log blocked command attempt to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "pattern": pattern_name,
        "description": description,
        "project_path": project_path
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def check_command(command: str) -> dict | None:
    """Check if command matches any dangerous pattern."""
    for rule in DANGEROUS_PATTERNS:
        if re.search(rule["pattern"], command, re.IGNORECASE):
            return rule
    return None


def main():
    """Main hook entry point."""
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If not JSON, allow the command
        sys.exit(0)
    
    # Extract command from tool use
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only check Bash tool
    if tool_name != "Bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    # Get project path if available
    project_path = input_data.get("project_path", os.getcwd())
    
    # Check for dangerous patterns
    matched_rule = check_command(command)
    
    if matched_rule:
        # Log the blocked attempt
        log_blocked_command(
            command=command,
            pattern_name=matched_rule["name"],
            description=matched_rule["description"],
            project_path=project_path
        )
        
        # Prepare rejection response
        response = {
            "decision": "reject",
            "message": f"""⚠️ **Dangerous Command Blocked**

**Command**: `{command[:100]}{'...' if len(command) > 100 else ''}`

**Pattern**: {matched_rule['name']}

**Reason**: {matched_rule['description']}

**Severity**: {matched_rule['severity'].upper()}

This command has been blocked for safety. If you're sure this is intentional, you can:
1. Review the command carefully
2. Ask the user to confirm
3. Use a safer alternative

**Log**: This attempt has been logged to `~/.claude/hooks/blocked.log`
"""
        }
        
        print(json.dumps(response))
        sys.exit(0)
    
    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
