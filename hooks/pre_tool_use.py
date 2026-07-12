#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands
"""

import os
import sys
import re
import logging
import json
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    filename=Path.home() / Path('.claude/hooks/blocked.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# List of destructive command patterns to block
DESTRUCTIVE_PATTERNS = [
    r'rm\s+-rf',
    r'DROP\s+TABLE',
    r'TRUNCATE',
    r'DELETE\s+FROM\s+\w+\s*$',
    r'git\s+push\s+.*--force'
]

def check_destructive_command(command):
    """Check if a command matches destructive patterns"""
    # Block commands that are considered destructive
    destructive_match = re.compile('|'.join(DESTRUCTIVE_PATTERNS), re.IGNORECASE)
    if destructive_match.search(command):
        return True
    return False

def block_destructive_commands():
    """Block destructive commands like rm -rf, DROP TABLE, etc."""
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if not command:
        return False
    
    # Check for destructive patterns
    if any(pattern in command for pattern in ['rm -rf', 'DROP TABLE', 'TRUNCATE', 'DELETE FROM']):
        return True
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pre_tool_use.py <command>")
        sys.exit(1)

    # Block commands that are considered destructive
    if any(pattern in sys.argv[1] for pattern in ['rm -rf', 'DROP TABLE', 'TRUNCATE', 'DELETE FROM']):
        with open('/Users/shanaboo/.cla