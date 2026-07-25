#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands in Claude Code.

This hook intercepts dangerous commands before execution and logs them.
Follows Claude Code hooks format: ~/.claude/hooks/
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf variants
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\s+', 'rm -rf: Recursive force delete'),
    (r'\brm\s+-rf\b', 'rm -rf: Recursive force delete'),
    
    # SQL destructive operations
    (r'\bDROP\s+TABLE\b', 'DROP TABLE: Destroys database table'),
    (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE: Removes all data from table'),
    (r'\bDELETE\s+FROM\s+\w+\s*;', 'DELETE FROM without WHERE: Removes all rows'),
    (r'\bDELETE\s+FROM\s+\w+\s*$', 'DELETE FROM without WHERE: Removes all rows'),
    
    # Git force push
    (r'\bgit\s+push\s+.*--force\b', 'git push --force: Overwrites remote history'),
    (r'\bgit\s+push\s+-f\b', 'git push -f: Overwrites remote history'),
    
    # Database drops
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE: Destroys entire database'),
    
    # Format/mkfs
    (r'\bmkfs\b', 'mkfs: Formats filesystem'),
    (r'\bdd\s+.*of=/dev/', 'dd to device: Can overwrite disk'),
]

# Compile patterns for performance
COMPILED_PATTERNS = [(re.compile(pattern, re.IGNORECASE), reason) for pattern, reason in DANGEROUS_PATTERNS]


def get_log_path() -> Path:
    """Get the path to the blocked commands log file."""
    hooks_dir = Path.home() / '.claude' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / 'blocked.log'


def log_blocked_command(command: str, reason: str, project_path: str) -> None:
    """Log a blocked command attempt to the log file."""
    log_path = get_log_path()
    timestamp = datetime.now().isoformat()
    
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += "-" * 80 + "\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str | None]:
    """
    Check if a command contains dangerous patterns.
    
    Returns:
        (is_safe, reason_if_blocked)
    """
    for pattern, reason in COMPILED_PATTERNS:
        if pattern.search(command):
            return False, reason
    return True, None


def is_command_safe(command: str) -> tuple[bool, str]:
    """Wrapper that returns (is_safe, reason) with non-optional reason."""
    is_safe, reason = check_command(command)
    return is_safe, reason or ""


def main():
    """Main hook entry point."""
    # Read input from stdin (Claude Code hook format)
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If not valid JSON, allow execution (fallback)
        sys.exit(0)
    
    # Extract command and context
    tool_name = hook_input.get('tool_name', '')
    tool_input = hook_input.get('tool_input', {})
    
    # Only check bash/terminal commands
    if tool_name not in ['bash', 'terminal', 'execute_command']:
        sys.exit(0)
    
    command = tool_input.get('command', '')
    if not command:
        sys.exit(0)
    
    # Get project path from environment or hook input
    project_path = os.environ.get('CLAUDE_PROJECT_PATH', 
                                   hook_input.get('project_path', 'unknown'))
    
    # Check if command is dangerous
    is_safe, reason = is_command_safe(command)
    
    if not is_safe:
        # Log the blocked attempt
        log_blocked_command(command, reason, project_path)
        
        # Output block message for Claude
        block_message = {
            'hookSpecificOutput': {
                'hookFailed': True,
                'errorMessage': f'🚫 BLOCKED: {reason}\n\n'
                               f'This command was blocked by the destructive command hook.\n'
                               f'If this is intentional, please review the command carefully '
                               f'and consider using a safer alternative.\n\n'
                               f'Blocked command: {command}'
            }
        }
        
        print(json.dumps(block_message))
        sys.exit(0)
    
    # Command is safe, allow execution
    sys.exit(0)


if __name__ == '__main__':
    main()
