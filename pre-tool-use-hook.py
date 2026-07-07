#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.
Install: mkdir -p ~/.claude/hooks/ && cp this_file ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import os
import re
import sys
import json
import logging
from datetime import datetime

# Configuration
HOOK_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")
ALWAYS_ALLOW = [
    "rm -rf node_modules",
    "rm -rf .next",
    "rm -rf build",
    "rm -rf dist",
    "rm -rf .git",
    "DROP TABLE IF EXISTS",
]

# Dangerous patterns - each is a (regex, description) pair
DANGEROUS_PATTERNS = [
    (re.compile(r'\brm\s+-rf\s+(?:/\s*|~\s*|/home\s*|/root\s*|/etc\s*|/var\s*|/usr\s*)', re.IGNORECASE), "Dangerous rm -rf targeting system directories"),
    (re.compile(r'\brm\s+-rf\s+(?:/\s*|~\s*)[\'"]?\s*$', re.IGNORECASE), "rm -rf at root/home level"),
    (re.compile(r'\bgit\s+push\s+--force\b', re.IGNORECASE), "Force push to git"),
    (re.compile(r'\bgit\s+push\s+origin\s+\+?\w+\s*:\s*\w+\s*--force\b', re.IGNORECASE), "Force push with refspec"),
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE SQL statement"),
    (re.compile(r'\bDROP\s+DATABASE\b', re.IGNORECASE), "DROP DATABASE SQL statement"),
    (re.compile(r'\bTRUNCATE\b', re.IGNORECASE), "TRUNCATE SQL statement"),
    (re.compile(r'\bDELETE\s+FROM\s+\w+\s*(?!\s*WHERE\b)', re.IGNORECASE), "DELETE FROM without WHERE clause"),
    (re.compile(r'\bUPDATE\s+\w+\s+SET\s+\w+(?:\s*=\s*[^,]+)?\s*(?!\s*WHERE\b)', re.IGNORECASE), "UPDATE without WHERE clause"),
    (re.compile(r'\bchmod\s+-R\s+777\b', re.IGNORECASE), "Recursive chmod 777"),
    (re.compile(r'\bchown\s+-R\b', re.IGNORECASE), "Recursive chown"),
    (re.compile(r'\bmkfs\.?\w*\b', re.IGNORECASE), "Filesystem creation"),
    (re.compile(r'\bdd\s+if=\s*/dev/[a-z]+\s+of=', re.IGNORECASE), "DD destructive operation"),
    (re.compile(r'\b:>\s*/\w+', re.IGNORECASE), "Truncate system file"),
    (re.compile(r'\b>\s*/dev/[a-z]+\b', re.IGNORECASE), "Write to raw device"),
    (re.compile(r'\bwget\s+(?:--no-check-certificate\s+)?-O\s+/', re.IGNORECASE), "Download to root path"),
    (re.compile(r'\bcurl\s+(?:-[sf]\s+)?-o\s+/', re.IGNORECASE), "Curl output to root path"),
    (re.compile(r'\bsudo\s+rm\b', re.IGNORECASE), "Sudo remove"),
    (re.compile(r'\bshutdown\b', re.IGNORECASE), "System shutdown"),
    (re.compile(r'\breboot\b', re.IGNORECASE), "System reboot"),
    (re.compile(r'\binit\s+0\b', re.IGNORECASE), "System halt"),
    (re.compile(r'\binit\s+6\b', re.IGNORECASE), "System reboot"),
    (re.compile(r'\bhadoop\s+fs\s+-rm\s+-r\b', re.IGNORECASE), "HDFS recursive delete"),
]

def setup_logging():
    """Ensure log directory and file exist."""
    os.makedirs(HOOK_DIR, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command is dangerous.
    Returns (is_blocked, reason).
    """
    for always in ALWAYS_ALLOW:
        if command.strip().startswith(always):
            return False, ""

    for pattern, description in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True, description

    return False, ""

def main():
    logger = setup_logging()
    
    # Read the command from stdin (Claude Code hooks protocol)
    input_data = sys.stdin.read().strip()
    
    try:
        payload = json.loads(input_data) if input_data else {}
        command = payload.get("command", "")
        full_command = payload.get("full_command", command)
    except json.JSONDecodeError:
        command = input_data
        full_command = input_data

    if not full_command:
        # No command to check
        print(json.dumps({"result": "allow", "reason": ""}))
        return

    is_blocked, reason = check_command(full_command)

    if is_blocked:
        logger.warning(f"BLOCKED | {reason} | command: {full_command[:200]}")
        result = {
            "result": "block",
            "reason": f"🚫 Blocked: {reason}. "
                       f"Command: '{full_command[:100]}...' "
                       f"Logged to {LOG_FILE}. "
                       f"Add to ALWAYS_ALLOW in the hook config if intentional."
        }
    else:
        result = {"result": "allow", "reason": ""}
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
