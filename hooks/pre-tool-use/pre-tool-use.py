#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook - Destructive Command Blocker
Prevents execution of dangerous bash commands that could cause data loss
"""
import json
import sys
import re
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # File deletion - must contain both -r and -f flags
    (r'rm\s+(-[rfRF]*\s+)*/+', 'Dangerous file deletion (rm -rf /)'),
    (r'rm\s+-[rfRF]*f[rfRF]*\s', 'Dangerous file deletion (rm -rf)'),
    (r'rm\s+-[rfRF]*r[rfRF]*f[rfRF]*\s', 'Dangerous file deletion (rm -rf)'),
    (r'rm\s+(-[rfRF]*\s+)*\*', 'Dangerous wildcard deletion (rm *)'),

    # SQL destructive operations
    (r'DROP\s+TABLE', 'SQL table deletion (DROP TABLE)'),
    (r'TRUNCATE\s+TABLE', 'SQL table truncation (TRUNCATE TABLE)'),
    (r'TRUNCATE\s+\w+', 'SQL table truncation (TRUNCATE)'),
    (r'DELETE\s+FROM\s+\w+\s*;', 'SQL deletion without WHERE clause'),
    (r'DELETE\s+FROM\s+\w+\s*$', 'SQL deletion without WHERE clause'),

    # Git force operations
    (r'git\s+push\s+[^;\n]*--force', 'Git force push'),
    (r'git\s+push\s+[^;\n]*-f\b', 'Git force push'),

    # System-level dangerous operations
    (r'mkfs\.', 'Filesystem formatting'),
    (r'dd\s+.*of=/dev/', 'Direct disk write'),
    (r':\(\)\{\s*:\|:&\s*\};:', 'Fork bomb'),
]

def load_tool_use_request():
    """Load the tool use request from stdin"""
    try:
        return json.load(sys.stdin)
    except Exception as e:
        # If we can't parse the request, allow it through
        sys.stderr.write(f"Error parsing tool use request: {e}\n")
        return None

def check_command_safety(command):
    """
    Check if a bash command is safe to execute
    Returns (is_safe, reason) tuple
    """
    # Normalize command for matching
    normalized = re.sub(r'\s+', ' ', command.strip())

    # Check against each dangerous pattern
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, reason

    return True, None

def log_blocked_command(command, reason, project_path):
    """Log blocked command attempt to ~/.claude/hooks/blocked.log"""
    log_dir = Path.home() / '.claude' / 'hooks'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'blocked.log'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += "-" * 80 + "\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to blocked.log: {e}\n")

def block_command(command, reason, project_path):
    """Block command execution and return error response"""
    # Log the blocked attempt
    log_blocked_command(command, reason, project_path)

    # Create clear error message for Claude
    error_msg = f"""🚫 COMMAND BLOCKED: {reason}

The following command was blocked because it could cause irreversible data loss:

    {command}

This command was logged to: ~/.claude/hooks/blocked.log

If you need to run this command, please:
1. Review the command carefully
2. Ensure you have backups
3. Run it manually outside of Claude Code

Alternatively, consider a safer approach to accomplish your goal.
"""

    # Return error response in Claude Code hook format
    response = {
        "error": error_msg,
        "tool_use_id": None,  # Will be set by Claude Code
        "blocked": True,
        "reason": reason
    }

    print(json.dumps(response, indent=2))
    sys.exit(1)

def allow_command(request):
    """Allow command to proceed"""
    # Pass through the original request unchanged
    print(json.dumps(request, indent=2))
    sys.exit(0)

def main():
    # Load the tool use request
    request = load_tool_use_request()

    if not request:
        # If we can't parse the request, allow it (fail open for safety)
        sys.exit(0)

    # Check if this is a Bash tool use
    tool_name = request.get('tool', {}).get('name', '')
    if tool_name != 'Bash':
        # Not a bash command, allow it
        allow_command(request)

    # Extract the bash command
    params = request.get('tool', {}).get('input', {})
    command = params.get('command', '')

    if not command:
        # No command specified, allow it
        allow_command(request)

    # Check if command is safe
    is_safe, reason = check_command_safety(command)

    if not is_safe:
        # Get project path for logging
        project_path = request.get('context', {}).get('cwd', 'unknown')

        # Block the command
        block_command(command, reason, project_path)

    # Command is safe, allow it
    allow_command(request)

if __name__ == '__main__':
    main()
