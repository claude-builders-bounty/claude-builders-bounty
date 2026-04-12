#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks dangerous bash commands.

Install:
    cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
    chmod +x ~/.claude/hooks/pre-tool-use

Or add to Claude Code config:
    "hooks": {
        "pre-tool-use": "python3 ~/.claude/hooks/pre-tool-use.py"
    }

Requires: Python 3.7+
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
HOOKS_DIR = Path.home() / ".claude" / "hooks"

# Dangerous patterns: (regex, friendly_name, severity)
DANGEROUS_PATTERNS = [
    # File destruction
    (r"rm\s+-rf\s+/\s*($|\||&)", "Recursive root deletion", "CRITICAL"),
    (r"rm\s+-rf\s+/tmp\s*($|\||&)", "Recursive /tmp deletion", "CRITICAL"),
    (r"rm\s+-rf\s+[a-zA-Z0-9_/.\-]+\s*($|\||&)", "Recursive deletion", "HIGH"),
    (r"rm\s+-rf\s+\.", "Delete current directory", "HIGH"),
    
    # Git destruction
    (r"git\s+push\s+--force\s*($|\||&)", "Force push to git", "HIGH"),
    (r"git\s+push\s+-f\s*($|\||&)", "Force push to git", "HIGH"),
    (r"rm\s+-rf\s+\.git", "Delete .git directory", "HIGH"),
    (r"git\s+reset\s+--hard\s+HEAD", "Hard reset git", "MEDIUM"),
    
    # Database destruction
    (r"DROP\s+TABLE\s+[a-zA-Z0-9_\.]*\s*;?\s*($|\||&)", "Drop SQL table", "CRITICAL"),
    (r"DROP\s+DATABASE\s+[a-zA-Z0-9_\.]*\s*;?\s*($|\||&)", "Drop SQL database", "CRITICAL"),
    (r"DROP\s+SCHEMA\s+[a-zA-Z0-9_\.]*\s*;?\s*($|\||&)", "Drop SQL schema", "CRITICAL"),
    (r"TRUNCATE\s+TABLE\s+[a-zA-Z0-9_\.]*\s*;?\s*($|\||&)", "Truncate SQL table", "HIGH"),
    (r"TRUNCATE\s+[a-zA-Z0-9_\.]+\s*;?\s*($|\||&)", "Truncate operation", "HIGH"),
    (r"DELETE\s+FROM\s+[a-zA-Z0-9_\.]+\s*;(?!\s*WHERE)", "SQL delete without WHERE", "HIGH"),
    (r"DELETE\s+FROM\s+[a-zA-Z0-9_\.]+\s+WHERE\s+1\s*=\s*1", "SQL delete all rows", "HIGH"),
    
    # System destruction
    (r"chmod\s+-R\s+777\s+/", "World-writable system files", "HIGH"),
    (r"mkfs", "Format disk", "CRITICAL"),
    (r"dd\s+if=", "Direct disk write", "CRITICAL"),
    (r":\(\)\s*:\s*\|\s*:\s*&\s*;", "Fork bomb", "CRITICAL"),
    
    # Network probes
    (r"curl\s+.*\|.*sh", "Pipe download to shell", "HIGH"),
    (r"wget\s+.*\|.*sh", "Pipe download to shell", "HIGH"),
    (r"bash\s+.*http", "Execute from URL", "HIGH"),
]


def log_blocked(timestamp: str, command: str, pattern: str, severity: str, project_path: str) -> None:
    """Log blocked attempt to file."""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED: '{command}' | Pattern: '{pattern}' ({severity}) | Path: {project_path}\n")


def format_blocked_message(command: str, pattern: str, severity: str) -> str:
    """Format the blocked message for Claude."""
    severity_icons = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
    }
    icon = severity_icons.get(severity, "⚠️")
    
    return f"""
╔══════════════════════════════════════════════════════════════╗
║  {icon} HOOK: Command Blocked                                      ║
║  Your command was blocked by the pre-tool-use security hook. ║
║                                                              ║
║  Blocked pattern: {pattern:<20}                         ║
║  Severity: {severity:<20}                         ║
║                                                              ║
║  Reason: This command could cause irreversible data loss or  ║
║  security compromise.                                       ║
║                                                              ║
║  If you believe this is a false positive, you can:         ║
║                                                              ║
║  1. Break down the operation into smaller, safe steps      ║
║  2. Use version control (git) instead of raw operations    ║
║  3. Ask the user to confirm before executing destructive   ║
║     operations                                             ║
║                                                              ║
║  This incident has been logged for security audit.           ║
╚══════════════════════════════════════════════════════════════╝
"""


def check_command(command: str, project_path: str) -> tuple[bool, str, str]:
    """
    Check if command is dangerous.
    Returns: (is_blocked, matched_pattern, severity)
    """
    for pattern, name, severity in DANGEROUS_PATTERNS:
        try:
            if re.search(pattern, command, re.IGNORECASE):
                return True, name, severity
        except re.error:
            # Skip invalid regex
            continue
    return False, "", ""


def main():
    """Main hook entry point."""
    # Read JSON input from Claude Code
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        # If we can't parse input, allow the command
        print(json.dumps({"continue": True}))
        return
    
    # Extract command from Claude Code hook input
    # Claude Code passes: { "command": "...", "project_path": "..." }
    command = input_data.get("command", "")
    project_path = input_data.get("project_path", "unknown")
    
    if not command:
        # Allow empty commands
        print(json.dumps({"continue": True}))
        return
    
    # Check if dangerous
    is_blocked, pattern, severity = check_command(command, project_path)
    
    if is_blocked:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_blocked(timestamp, command, pattern, severity, project_path)
        
        # Output blocked message
        message = format_blocked_message(command, pattern, severity)
        
        # Claude Code expects hook to return { "blocked": true, "message": "..." }
        print(json.dumps({
            "blocked": True,
            "message": message.strip()
        }))
        sys.exit(1)
    
    # Allow safe commands
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
