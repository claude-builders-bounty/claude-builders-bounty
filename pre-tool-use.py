#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands (Python version)
Place this file at: ~/.claude/hooks/pre-tool-use.py

Installation:
  1. pip install pyyaml
  2. cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
"""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)

DANGEROUS_PATTERNS = [
    re.compile(r'\brm\s+(-[rf]+\s+)+', re.IGNORECASE),
    re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
    re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
    re.compile(r'\bgit\s+push\s+(-f|--force)\b', re.IGNORECASE),
    re.compile(r'\bDELETE\s+FROM\b.*(?<!WHERE)', re.IGNORECASE),
]

BLOCKED_MESSAGE = """🚫 BLOCKED: Dangerous command intercepted for safety.

Blocked patterns:
- rm -rf (recursive force delete)
- DROP TABLE (SQL table destruction)
- TRUNCATE (table truncation)
- git push --force (forced overwrite)
- DELETE FROM without WHERE (mass deletion)

Safer alternatives:
- Use 'trash-cli' instead of 'rm -rf'
- Add --interactive flag to rm
- Use git push --force-with-lease instead of --force
- Always include WHERE clause in DELETE statements

Project: {project}
Timestamp: {timestamp}
""".strip()


def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any dangerous pattern.
    
    Returns (is_blocked, message).
    """
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            # Special check for DELETE FROM without WHERE
            if 'DELETE FROM' in command.upper() and 'WHERE' not in command.upper():
                log_block(command)
                return True, BLOCKED_MESSAGE.format(
                    project=os.getcwd(),
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            # General block
            log_block(command)
            return True, BLOCKED_MESSAGE.format(
                project=os.getcwd(),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    return False, ""


def log_block(command: str):
    """Log blocked command attempt."""
    log_entry = (
        f"[{datetime.now(timezone.utc).isoformat()}] BLOCKED: '{command}' "
        f"| Project: {os.getcwd()}\n"
    )
    BLOCKED_LOG.write_text(log_entry, mode='a')


def main():
    """Main entry point for Claude Code hook."""
    # Read command from environment variable or stdin
    command = os.environ.get("CLAUDE_CODE_COMMAND", "")
    
    if not command:
        # Read from stdin if available
        if not sys.stdin.isatty():
            command = sys.stdin.read().strip()
    
    if not command:
        sys.exit(0)
    
    is_blocked, message = check_command(command)
    
    if is_blocked:
        print(message)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
