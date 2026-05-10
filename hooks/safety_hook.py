#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands
Intercepts dangerous bash commands before execution.
"""

import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path

# --- Configuration ---
BLOCKED_PATTERNS = [
    # Destructive file operations
    (r'rm\s+(-[rfRF]+\s+|--recursive|--force)', "Recursive/forced file deletion"),
    (r'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r', "Recursive forced deletion"),
    (r'rmdir\s+/[sS]', "Recursive directory removal"),
    
    # Destructive SQL
    (r'DROP\s+TABLE', "Dropping database table"),
    (r'DROP\s+DATABASE', "Dropping database"),
    (r'TRUNCATE\s+TABLE', "Truncating table"),
    (r'DELETE\s+FROM\s+(?!.*WHERE)', "DELETE without WHERE clause"),
    (r'ALTER\s+TABLE.*DROP', "Dropping table column"),
    
    # Destructive git
    (r'git\s+push\s+.*--force', "Force push"),
    (r'git\s+push\s+.*-f\s', "Force push (short flag)"),
    (r'git\s+reset\s+.*--hard', "Hard reset"),
    (r'git\s+clean\s+.*-f', "Force clean"),
    (r'git\s+branch\s+-[dD]\s', "Deleting branch"),
    
    # Destructive system
    (r'chmod\s+777', "Overly permissive permissions"),
    (r'curl.*\|\s*(sudo\s+)?(bash|sh)', "Piping to shell"),
    (r'wget.*\|\s*(sudo\s+)?(bash|sh)', "Piping to shell"),
    (r'mkfs\.', "Formatting filesystem"),
    (r'dd\s+.*of=/dev/', "Writing to device"),
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

def log_blocked(command: str, reason: str, project_path: str):
    """Log blocked command to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  Command: {command}\n")
        f.write(f"  Project: {project_path}\n\n")

def check_command(command: str) -> str | None:
    """Check if command matches any blocked pattern. Returns reason or None."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return None

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only check Bash tool
    if tool_name != "Bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    project_path = tool_input.get("cwd", os.getcwd())
    
    if not command:
        sys.exit(0)
    
    reason = check_command(command)
    if reason:
        log_blocked(command, reason, project_path)
        print(f"\n🚫 BLOCKED: {reason}", file=sys.stderr)
        print(f"   Command: {command}", file=sys.stderr)
        print(f"   This command was blocked by the safety hook.", file=sys.stderr)
        print(f"   Logged to: {LOG_FILE}", file=sys.stderr)
        sys.exit(2)  # Non-zero = block
    
    sys.exit(0)  # Allow

if __name__ == "__main__":
    main()
