#!/usr/bin/env python3
"""
Pre-tool-use Hook: Safety Guard
Blocks destructive bash commands before execution.

Installation:
    cp safety-hook.py ~/.claude/hooks/pre-tool-use/safety-hook.py
    chmod +x ~/.claude/hooks/pre-tool-use/safety-hook.py
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path


# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # File system destruction
    (r'\brm\s+(-[rf]+\s+|--recursive\s+|--force\s+).*\S', 'rm -rf (recursive force delete)'),
    (r'\brm\s+.*\s-[rf]+', 'rm with recursive/force flags'),
    
    # Database destruction
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'DROP TABLE/DATABASE/SCHEMA'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'TRUNCATE table'),
    (r'\bDELETE\s+FROM\s+\w+\s*;', 'DELETE FROM without WHERE clause'),
    (r'\bDELETE\s+FROM\s+\w+\s*$', 'DELETE FROM without WHERE clause'),
    
    # Git force operations
    (r'\bgit\s+push\s+.*--force', 'git push --force'),
    (r'\bgit\s+push\s+.*-f\b', 'git push -f (force)'),
    (r'\bgit\s+reset\s+--hard', 'git reset --hard (destructive)'),
    
    # System commands
    (r'\bdd\s+if=.*of=/dev/', 'dd to device (destructive)'),
    (r'\bmkfs\.', 'format filesystem'),
    (r'\bshutdown\b', 'system shutdown'),
    (r'\breboot\b', 'system reboot'),
    (r'\bhalt\b', 'system halt'),
    
    # Environment destruction
    (r'\bexport\s+PATH\s*=\s*["\']?/', 'Overwrite PATH'),
    (r'\bunset\s+PATH\b', 'Unset PATH'),
    
    # Fork bomb
    (r':\(\)\s*\{\s*:\|:&\s*\}\s*;:', 'Fork bomb detected'),
    
    # Wipe commands
    (r'\bwipefs\b', 'wipe filesystem signature'),
    (r'\bshred\b', 'shred file (secure delete)'),
    
    # Python destructive
    (r'__import__\s*\(\s*["\']os["\']\s*\)\s*\.\s*system', 'Python os.system call'),
    (r'subprocess\.(call|run|Popen)\s*\([^)]*rm\s', 'Python subprocess rm call'),
    
    # Node destructive
    (r'child_process\.(exec|spawn)\s*\([^)]*rm\s', 'Node.js child_process rm'),
    
    # Curl/wget pipe to shell (dangerous)
    (r'curl\s+.*\|\s*(bash|sh)', 'curl pipe to shell (potential malware)'),
    (r'wget\s+.*\|\s*(bash|sh)', 'wget pipe to shell (potential malware)'),
]


def get_log_path():
    """Get the path to the blocked commands log file."""
    log_dir = Path.home() / '.claude' / 'hooks'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / 'blocked.log'


def log_blocked_command(command: str, reason: str, project_path: str = None):
    """Log a blocked command attempt."""
    log_path = get_log_path()
    timestamp = datetime.now().isoformat()
    
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n"
    log_entry += f"  Command: {command}\n"
    if project_path:
        log_entry += f"  Project: {project_path}\n"
    log_entry += "\n"
    
    with open(log_path, 'a') as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command contains dangerous patterns.
    Returns (is_dangerous, reason).
    """
    # Normalize command for checking
    normalized = command.strip()
    
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, description
    
    return False, ""


def main():
    """Main hook function."""
    # Read the hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If not valid JSON, just pass through
        sys.exit(0)
    
    # Extract relevant information
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    project_path = input_data.get('cwd', os.getcwd())
    
    # Only check bash commands
    if tool_name not in ['bash', 'exec']:
        sys.exit(0)
    
    # Get the command to check
    command = tool_input.get('command', '')
    if not command:
        sys.exit(0)
    
    # Check for dangerous patterns
    is_dangerous, reason = check_command(command)
    
    if is_dangerous:
        # Log the blocked attempt
        log_blocked_command(command, reason, project_path)
        
        # Return error to block the command
        error_message = {
            "error": f"🛡️ Safety Guard: Command blocked for safety",
            "details": f"The command '{command[:100]}...' was blocked because it matches a dangerous pattern: {reason}",
            "suggestion": "If you're sure this is safe, you can bypass this check by running the command directly in your terminal.",
            "logged_to": str(get_log_path())
        }
        
        print(json.dumps(error_message), file=sys.stderr)
        sys.exit(2)  # Exit code 2 tells Claude the command was blocked
    
    # Command is safe, allow execution
    sys.exit(0)


if __name__ == '__main__':
    main()