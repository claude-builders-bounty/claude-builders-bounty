#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Block destructive bash commands.

Place at: ~/.claude/hooks/block-destructive-commands.py
Make executable: chmod +x ~/.claude/hooks/block-destructive-commands.py

This hook intercepts bash tool calls and blocks known destructive patterns.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Patterns that are always blocked
DANGEROUS_PATTERNS = [
    # rm -rf (and variants like rm -rfv, rm -r -f)
    (r'\brm\s+(?:-[a-zA-Z]*\s+)*-?[a-zA-Z]*f[a-zA-Z]*\s+(?:-[a-zA-Z]*\s+)*\S+', 'rm -rf: recursive force deletion'),
    
    # DROP TABLE
    (r'\bDROP\s+TABLE\b', 'DROP TABLE: destructive SQL operation'),
    
    # git push --force (and --force-with-lease)
    (r'\bgit\s+push\s+(?:-[a-zA-Z]*\s+)*--force(?:\b|$)', 'git push --force: overwrites remote history'),
    (r'\bgit\s+push\s+(?:-[a-zA-Z]*\s+)*-f(?:\b|$)', 'git push -f: overwrites remote history'),
    
    # TRUNCATE TABLE
    (r'\bTRUNCATE\s+(?:TABLE\s+)?\w+', 'TRUNCATE: irreversible data removal'),
]

# Patterns that are blocked only without a WHERE clause
DELETE_PATTERN = re.compile(r'\bDELETE\s+FROM\s+\w+', re.IGNORECASE)


def get_log_path() -> Path:
    """Return the path to the blocked attempts log file."""
    hooks_dir = Path.home() / '.claude' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / 'blocked.log'


def log_blocked(command: str, reason: str) -> None:
    """Log a blocked command attempt with timestamp and project path."""
    log_path = get_log_path()
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    project_path = os.getcwd()
    
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'{timestamp} | {command} | {project_path}\n')
    except OSError:
        pass  # Best effort logging


def is_dangerous(command: str) -> tuple[bool, str]:
    """Check if a command matches a dangerous pattern. Returns (is_blocked, reason)."""
    # Check DELETE FROM without WHERE
    if DELETE_PATTERN.search(command):
        # Check if there's a WHERE clause after the table name
        after_delete = command[command.upper().find('FROM'):]
        if 'WHERE' not in after_delete.upper():
            return True, 'DELETE FROM without WHERE: would delete all rows'
    
    # Check always-dangerous patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    
    return False, ''


def main() -> None:
    """Main entry point for the hook."""
    # Read the tool use request from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Allow on parse error
    
    # Only intercept bash tool calls
    if data.get('tool_name') != 'bash':
        sys.exit(0)
    
    command = data.get('params', {}).get('command', '')
    
    blocked, reason = is_dangerous(command)
    if blocked:
        log_blocked(command, reason)
        print(f'[BLOCKED] This command was blocked for safety: {reason}', file=sys.stderr)
        print(f'Command: {command}', file=sys.stderr)
        print('Please use a safer alternative or confirm this action is intentional.', file=sys.stderr)
        sys.exit(1)  # Non-zero exit blocks the tool use
    
    sys.exit(0)


if __name__ == '__main__':
    main()