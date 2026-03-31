#!/usr/bin/env python3
"""
Pre-Tool-Use Security Hook for Claude Code
Blocks dangerous bash commands before execution.

Installation:
  mkdir -p ~/.claude/hooks
  cp pre_tool_hook.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre_tool_hook.py
"""

import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

# Configuration file path
CONFIG_FILE = Path.home() / ".claude" / "hooks" / "hook_config.json"

# Default blocked patterns
DEFAULT_CONFIG = {
    "blocked_patterns": [
        {
            "pattern": r"rm\s+(-[rf]+\s+|-\w*[rf]\w*\s+)*\/",
            "description": "rm -rf / (destructive file deletion)",
            "severity": "critical"
        },
        {
            "pattern": r"rm\s+(-[rf]+\s+|-\w*[rf]\w*\s+)*~",
            "description": "rm -rf ~ (home directory deletion)",
            "severity": "critical"
        },
        {
            "pattern": r"rm\s+(-[rf]+\s+|-\w*[rf]\w*\s+)*\*",
            "description": "rm -rf * (wildcard deletion)",
            "severity": "critical"
        },
        {
            "pattern": r"DROP\s+TABLE",
            "description": "DROP TABLE (SQL destructive operation)",
            "severity": "critical"
        },
        {
            "pattern": r"TRUNCATE\s+TABLE",
            "description": "TRUNCATE TABLE (SQL destructive operation)",
            "severity": "critical"
        },
        {
            "pattern": r"DELETE\s+FROM",
            "description": "DELETE FROM without WHERE (SQL destructive operation)",
            "severity": "warning",
            "require_where": True
        },
        {
            "pattern": r"git\s+push\s+.*--force",
            "description": "git push --force (destructive git operation)",
            "severity": "warning"
        },
        {
            "pattern": r"git\s+push\s+.*-f\b",
            "description": "git push -f (shorthand force push)",
            "severity": "warning"
        },
        {
            "pattern": r"dd\s+.*of=/dev/[sh]d",
            "description": "dd to disk device (destructive disk operation)",
            "severity": "critical"
        },
        {
            "pattern": r">\s*/dev/[sh]d",
            "description": "Redirect to disk device (destructive)",
            "severity": "critical"
        },
        {
            "pattern": r"mkfs",
            "description": "mkfs (filesystem creation - destructive)",
            "severity": "critical"
        },
        {
            "pattern": r"wipefs\s",
            "description": "wipefs (filesystem wiping)",
            "severity": "critical"
        },
        {
            "pattern": r"shred\s",
            "description": "shred (secure file deletion)",
            "severity": "warning"
        },
        {
            "pattern": r":(){ :|:& };:",
            "description": "Fork bomb",
            "severity": "critical"
        },
        {
            "pattern": r"chmod\s+(-R\s+)?000\s+/",
            "description": "chmod 000 / (lock entire system)",
            "severity": "critical"
        },
        {
            "pattern": r"chown\s+.*:.*\s+/",
            "description": "chown on root (system corruption)",
            "severity": "critical"
        }
    ],
    "log_file": str(Path.home() / ".claude" / "hooks" / "blocked.log"),
    "enabled": True,
    "exit_on_block": True
}

def load_config():
    """Load configuration from file, creating default if not exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                merged = DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG

def log_blocked_command(command, pattern_info, project_path="unknown"):
    """Log blocked command attempt to file."""
    config = load_config()
    log_file = Path(config.get("log_file", DEFAULT_CONFIG["log_file"]))
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "pattern": pattern_info.get("pattern", "unknown"),
        "description": pattern_info.get("description", "unknown"),
        "severity": pattern_info.get("severity", "warning"),
        "project_path": project_path
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def check_for_where_clause(command, pattern):
    """Check if DELETE FROM has a WHERE clause."""
    if "require_where" in pattern:
        # Check if WHERE appears after DELETE FROM
        if not re.search(r"WHERE\s+", command, re.IGNORECASE):
            return False
    return True

def check_command(command, config):
    """Check if command matches any blocked pattern."""
    if not config.get("enabled", True):
        return None
    
    for pattern_info in config.get("blocked_patterns", []):
        pattern = pattern_info.get("pattern", "")
        if re.search(pattern, command, re.IGNORECASE):
            # Special handling for patterns requiring WHERE clause
            if not check_for_where_clause(command, pattern_info):
                return pattern_info
            elif "require_where" not in pattern_info:
                return pattern_info
    
    return None

def format_error_message(pattern_info, command):
    """Format user-friendly error message."""
    description = pattern_info.get("description", "potentially destructive operation")
    severity = pattern_info.get("severity", "warning")
    
    emoji = "🚫" if severity == "critical" else "⚠️"
    
    message = f"""
{emoji} SECURITY BLOCK: Command blocked by pre-tool-use hook

Reason: {description}

Attempted command: {command[:100]}{'...' if len(command) > 100 else ''}

This command was blocked to prevent unintended data loss or system damage.
If you intentionally want to run this command, you can:

1. Modify ~/.claude/hooks/hook_config.json to adjust blocked patterns
2. Temporarily disable the hook by setting "enabled": false in the config

Blocked attempts are logged to: ~/.claude/hooks/blocked.log
"""
    return message.strip()

def main():
    """Main entry point for hook."""
    # Read hook input from Claude Code
    # Format: JSON via stdin containing tool name and arguments
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If not JSON, treat as raw command string
        input_data = {"tool": "bash", "arguments": {"command": sys.stdin.read()}}
    
    # Extract command from various input formats
    command = ""
    tool_name = input_data.get("tool", "unknown")
    project_path = input_data.get("project_path", os.getcwd())
    
    # Handle different input formats
    if "arguments" in input_data:
        command = input_data["arguments"].get("command", "")
    elif "command" in input_data:
        command = input_data["command"]
    elif "input" in input_data:
        command = input_data["input"]
    
    if not command:
        # No command to check, allow
        sys.exit(0)
    
    # Load configuration and check command
    config = load_config()
    blocked_pattern = check_command(command, config)
    
    if blocked_pattern:
        # Log the blocked attempt
        log_blocked_command(command, blocked_pattern, project_path)
        
        # Output error message
        error_msg = format_error_message(blocked_pattern, command)
        print(error_msg, file=sys.stderr)
        
        # Exit with non-zero to block
        if config.get("exit_on_block", True):
            sys.exit(1)
    
    # Command allowed
    sys.exit(0)

if __name__ == "__main__":
    main()