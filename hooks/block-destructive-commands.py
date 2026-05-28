#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous commands before execution and logs blocked attempts.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    # rm -rf / rm -fr variants
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s', "rm -rf: Recursive force delete"),
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)$', "rm -rf: Recursive force delete"),
    (r'\brm\s+--recursive\s+--force', "rm --recursive --force: Recursive force delete"),
    (r'\brm\s+--force\s+--recursive', "rm --force --recursive: Recursive force delete"),
    
    # DROP TABLE
    (r'\bDROP\s+TABLE\b', "DROP TABLE: Deletes entire database table"),
    (r'\bDROP\s+TABLE\s+IF\s+EXISTS\b', "DROP TABLE IF EXISTS: Deletes table if it exists"),
    
    # TRUNCATE
    (r'\bTRUNCATE\s+TABLE\b', "TRUNCATE TABLE: Deletes all rows from table"),
    (r'\bTRUNCATE\b', "TRUNCATE: Deletes all data from table"),
    
    # DELETE FROM without WHERE clause
    (r'\bDELETE\s+FROM\s+\w+\s*;', "DELETE FROM without WHERE: Deletes all rows"),
    (r'\bDELETE\s+FROM\s+\w+\s*$', "DELETE FROM without WHERE: Deletes all rows"),
    
    # git push --force
    (r'\bgit\s+push\s+.*--force', "git push --force: Force push overwrites remote history"),
    (r'\bgit\s+push\s+.*-f\b', "git push -f: Force push overwrites remote history"),
    (r'\bgit\s+push\s+--force-with-lease', "git push --force-with-lease: Force push with lease check"),
    
    # mkfs (format filesystem)
    (r'\bmkfs\b', "mkfs: Formats filesystem, destroys all data"),
    
    # dd (disk destroyer)
    (r'\bdd\s+.*of=/dev/', "dd to device: Writes directly to device, can destroy data"),
    
    # chmod 777 (security risk)
    (r'\bchmod\s+777\b', "chmod 777: Grants full permissions to everyone (security risk)"),
    
    # chown -R (recursive ownership change)
    (r'\bchown\s+-R\b', "chown -R: Recursive ownership change"),
    
    # shutdown/reboot
    (r'\b(shutdown|reboot|poweroff)\b', "System shutdown/reboot: Interrupts system operation"),
    
    # fork bomb
    (r':\(\)\{.*\|.*&\}', "Fork bomb: Spawns infinite processes"),
]

# Safe patterns that might match dangerous patterns but are OK
SAFE_PATTERNS = [
    r'\bhistory\b',  # history command
    r'\bgrep\b',  # grep
    r'\bawk\b',  # awk
    r'\bsed\b',  # sed
    r'\bcat\b.*\|.*\bgrep\b',  # cat | grep
    r'\bman\b',  # man pages
    r'\bhelp\b',  # help
    r'--help',  # --help flag
]


def get_log_path() -> Path:
    """Get path to the blocked commands log file."""
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "blocked.log"


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    """Log a blocked command attempt to the log file."""
    log_path = get_log_path()
    timestamp = datetime.now().isoformat()
    
    log_entry = f"[{timestamp}] BLOCKED\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += f"  Reason: {reason}\n"
    log_entry += f"{'='*60}\n"
    
    with open(log_path, "a") as f:
        f.write(log_entry)


def is_safe_command(command: str) -> bool:
    """Check if command matches any safe patterns."""
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def check_dangerous_command(command: str) -> str | None:
    """
    Check if a command matches any dangerous patterns.
    Returns the reason if dangerous, None if safe.
    """
    # Skip if command matches safe patterns
    if is_safe_command(command):
        return None
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    
    return None


def main():
    """
    Main hook entry point.
    
    Claude Code hooks receive JSON on stdin with:
    {
        "tool": "bash",
        "tool_input": {
            "command": "the command to run"
        },
        "cwd": "/path/to/project"
    }
    
    Exit codes:
    - 0: Allow the command
    - 2: Block the command (stderr message shown to Claude)
    """
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        
        # Parse JSON input
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            # If not valid JSON, allow the command
            sys.exit(0)
        
        # Extract command and project path
        tool = data.get("tool", "")
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")
        project_path = data.get("cwd", os.getcwd())
        
        # Only check bash/shell commands
        if tool not in ("bash", "shell", "execute"):
            sys.exit(0)
        
        # Skip empty commands
        if not command.strip():
            sys.exit(0)
        
        # Check for dangerous commands
        reason = check_dangerous_command(command)
        
        if reason:
            # Log the blocked attempt
            log_blocked_attempt(command, project_path, reason)
            
            # Print error message to stderr (shown to Claude)
            print(f"⚠️ BLOCKED: This command was intercepted by the destructive command hook.", file=sys.stderr)
            print(f"Reason: {reason}", file=sys.stderr)
            print(f"Command: {command}", file=sys.stderr)
            print(f"\nThis command was blocked to prevent potential data loss or system damage.", file=sys.stderr)
            print(f"If you really need to run this command, please ask the user for explicit permission.", file=sys.stderr)
            
            # Exit with code 2 to block the command
            sys.exit(2)
        
        # Command is safe, allow it
        sys.exit(0)
        
    except Exception as e:
        # On any error, allow the command (don't break Claude Code)
        print(f"Hook error (allowing command): {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
