#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook

This hook intercepts dangerous commands before execution and logs blocked attempts.
Place this in ~/.claude/hooks/pre_tool_use.py

Dangerous patterns blocked:
- rm -rf, rm -fr, rm /*, rm ~/*
- DROP TABLE, DELETE FROM, TRUNCATE
- chmod -R 777, chown -R
- dd if=/dev/zero, :(){:|:&};:
- curl/sh/wget piped to bash/sh
- sudo with dangerous commands
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

# Configuration
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (r'rm\s+(-[rf]+\s+)*(/\s*|~/\s*|\*\s*)', 'DANGEROUS_RM: Attempt to remove root/home directory'),
    (r'rm\s+(-[rf]+\s+)+', 'DANGEROUS_RM: Recursive force delete detected'),
    (r'rm\s+-[a-z]*r[a-z]*\s+-[a-z]*f[a-z]*', 'DANGEROUS_RM: Recursive force delete detected'),
    (r'rm\s+-[a-z]*f[a-z]*\s+-[a-z]*r[a-z]*', 'DANGEROUS_RM: Recursive force delete detected'),
    
    # SQL injection/destruction
    (r'DROP\s+TABLE\s+', 'DANGEROUS_SQL: DROP TABLE detected'),
    (r'DELETE\s+FROM\s+\w+\s*(WHERE\s+1\s*=\s*1|;|--)', 'DANGEROUS_SQL: Mass DELETE detected'),
    (r'TRUNCATE\s+(TABLE\s+)?\w+', 'DANGEROUS_SQL: TRUNCATE detected'),
    
    # Permission changes
    (r'chmod\s+(-R\s+)?777', 'DANGEROUS_PERM: Setting world-writable permissions'),
    (r'chown\s+(-R\s+)?\w+:\w+\s+/', 'DANGEROUS_PERM: Changing ownership of root directory'),
    
    # Disk destruction
    (r'dd\s+if=/dev/zero\s+of=/', 'DANGEROUS_DISK: Disk zeroing detected'),
    (r'mkfs\.', 'DANGEROUS_DISK: Filesystem creation detected'),
    
    # Fork bombs
    (r':\(\)\{\s*:\|\:&\s*\}\s*;', 'DANGEROUS_FORK: Fork bomb detected'),
    (r'\(\)\s*\{\s*:\|\:&\s*\}\s*;', 'DANGEROUS_FORK: Fork bomb detected'),
    
    # Remote code execution
    (r'curl\s+.*\|\s*(ba)?sh', 'DANGEROUS_RCE: Curl piped to shell'),
    (r'wget\s+.*\|\s*(ba)?sh', 'DANGEROUS_RCE: Wget piped to shell'),
    (r'curl\s+.*\|\s*bash', 'DANGEROUS_RCE: Curl piped to bash'),
    (r'curl\s+.*\|\s*sh', 'DANGEROUS_RCE: Curl piped to sh'),
    
    # Sudo abuse
    (r'sudo\s+rm\s+(-[rf]+\s+)*(/\s*|~/\s*)', 'DANGEROUS_SUDO: Sudo rm on root/home'),
    (r'sudo\s+chmod\s+(-R\s+)?777', 'DANGEROUS_SUDO: Sudo chmod 777'),
]

def log_blocked(command: str, reason: str) -> None:
    """Log blocked command to file"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"🚫 BLOCKED: {reason}", file=sys.stderr)
    print(f"   Command: {command}", file=sys.stderr)
    print(f"   Logged to: {LOG_FILE}", file=sys.stderr)

def check_command(command: str) -> Tuple[bool, str]:
    """Check if command matches any dangerous pattern"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    """Main hook entry point"""
    # Read input from stdin (Claude Code passes tool use request as JSON)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(0)  # Allow on parse error
    
    # Extract command from tool use request
    tool_use = input_data.get('tool_use', {})
    command = ""
    
    # Handle different tool types
    if tool_use.get('type') == 'shell':
        command = tool_use.get('command', '')
    elif tool_use.get('type') == 'exec':
        command = tool_use.get('command', '') or tool_use.get('args', [])
        if isinstance(command, list):
            command = ' '.join(command)
    else:
        # Not a shell command, allow
        sys.exit(0)
    
    if not command:
        sys.exit(0)
    
    # Check for dangerous patterns
    is_dangerous, reason = check_command(str(command))
    
    if is_dangerous:
        log_blocked(str(command), reason)
        sys.exit(1)  # Block the command
    
    # Command is safe, allow it
    sys.exit(0)

if __name__ == '__main__':
    main()
