#!/usr/bin/env python3
"""
Pre-tool-use Hook: Block Destructive Bash Commands
Bounty: claude-builders-bounty/claude-builders-bounty #3
Author: FanLi (范蠡)
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path

# Configuration
HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    {
        "pattern": r"rm\s+(-[rf]+\s+)*(/|~|\*|\.\.)",
        "reason": "Potentially destructive rm command targeting root, home, or parent directories",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"rm\s+-rf\s+",
        "reason": "Recursive force delete - extremely dangerous",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"DROP\s+TABLE\s+",
        "reason": "SQL DROP TABLE command - will delete entire table",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"TRUNCATE\s+",
        "reason": "SQL TRUNCATE command - will delete all data in table",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"DELETE\s+FROM\s+\w+\s*(;|WHERE\s+1\s*=|WHERE\s+true)",
        "reason": "SQL DELETE without proper WHERE clause - may delete all rows",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"git\s+push\s+--force",
        "reason": "Force push can overwrite remote history and lose others' work",
        "severity": "HIGH"
    },
    {
        "pattern": r"git\s+push\s+-f\b",
        "reason": "Force push (shorthand) can overwrite remote history",
        "severity": "HIGH"
    },
]

def log_blocked(command: str, reason: str, severity: str) -> None:
    """Log blocked attempt to blocked.log"""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()
    
    log_entry = f"[{timestamp}] [{severity}] {reason}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n"
    log_entry += "-" * 60 + "\n"
    
    with open(BLOCKED_LOG, "a") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str, str]:
    """
    Check if command matches any dangerous pattern.
    Returns: (is_blocked, reason, severity)
    """
    for pattern_info in DANGEROUS_PATTERNS:
        if re.search(pattern_info["pattern"], command, re.IGNORECASE):
            return True, pattern_info["reason"], pattern_info["severity"]
    return False, "", ""

def main():
    """Main hook entry point"""
    # Read command from stdin or argument
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = sys.stdin.read().strip()
    
    if not command:
        print(json.dumps({"allow": True, "message": "No command provided"}))
        return
    
    is_blocked, reason, severity = check_command(command)
    
    if is_blocked:
        log_blocked(command, reason, severity)
        
        # Output block message in Claude Code hook format
        result = {
            "allow": False,
            "message": f"🚫 BLOCKED ({severity}): {reason}",
            "details": {
                "command": command,
                "reason": reason,
                "severity": severity,
                "logged_to": str(BLOCKED_LOG)
            }
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    else:
        # Command is safe
        result = {
            "allow": True,
            "message": "Command passed safety check"
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)

if __name__ == "__main__":
    main()
