#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.

This hook intercepts dangerous bash commands before they are executed
by Claude Code, preventing accidental data loss.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# Patterns that are always blocked (unconditional destructive commands)
ALWAYS_BLOCKED = [
    r"rm\s+(-[a-zA-Z]*f|--force).*-r",  # rm -rf, rm -fr, etc.
    r"rm\s+-[a-zA-Z]*r.*-f",            # rm -r...f variations
    r"git\s+push\s+.*--force",           # git push --force
    r"git\s+push\s+-f",                  # git push -f
    r"DROP\s+TABLE",                     # SQL DROP TABLE
    r"DROP\s+DATABASE",                 # SQL DROP DATABASE
    r"TRUNCATE\s+TABLE",                 # SQL TRUNCATE
    r"TRUNCATE\s+",                      # SQL TRUNCATE without TABLE
]

# Patterns that require additional checks (conditional)
CONDITIONAL_PATTERNS = [
    # DELETE FROM without WHERE
    (r"DELETE\s+FROM\s+\S+", r"WHERE"),
]


def get_log_path() -> Path:
    """Get the path to the blocked log file."""
    hooks_dir = Path(__file__).parent
    return hooks_dir / "blocked.log"


def log_blocked_attempt(command: str, project_path: str) -> None:
    """Log a blocked command attempt to the log file."""
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {command.strip()} | Project: {project_path}\n"
    
    with open(log_path, "a") as f:
        f.write(log_entry)


def is_bash_command(tool_name: str, tool_input: dict) -> bool:
    """Check if the tool is a bash command execution."""
    if tool_name not in ("bash", "Bash"):
        return False
    
    # Check if it's a bash command (not a different shell)
    command = tool_input.get("command", "")
    return bool(command)


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command is destructive.
    
    Returns:
        tuple of (is_blocked, reason)
    """
    command_upper = command.upper()
    
    # Check always-blocked patterns
    for pattern in ALWAYS_BLOCKED:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Command matches blocked pattern: {pattern}"
    
    # Check conditional patterns
    for pattern, required in CONDITIONAL_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            if not re.search(required, command, re.IGNORECASE):
                return True, f"Command matches blocked pattern: DELETE FROM without WHERE clause"
    
    return False, ""


def main():
    """Main hook entry point."""
    # Read the hook input from stdin (Claude Code passes tool info as JSON)
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not a valid JSON, pass through
        sys.exit(0)
    
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    
    # Only check bash commands
    if not is_bash_command(tool_name, tool_input):
        sys.exit(0)
    
    command = tool_input.get("command", "")
    
    is_blocked, reason = check_command(command)
    
    if is_blocked:
        project_path = os.getcwd()
        log_blocked_attempt(command, project_path)
        
        # Output the block message to stderr so Claude sees it
        print(f"\n🚫 BLOCKED: Destructive command prevented for safety.\n   Reason: {reason}\n   Command: {command}\n   This command has been logged to ~/.claude/hooks/blocked.log\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()