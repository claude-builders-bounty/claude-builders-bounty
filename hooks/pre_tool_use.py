#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
=====================================

Blocks destructive bash commands before execution.
Protects against accidental data loss and dangerous operations.

Installation:
    mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/
    chmod +x ~/.claude/hooks/pre_tool_use.py

Author: Security Researcher
License: MIT
Version: 1.0.0
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
HOOK_NAME = "pre_tool_use"
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Dangerous command patterns (regex)
DANGEROUS_PATTERNS = {
    # Filesystem destruction
    r"\brm\s+(-[rf]+\s+|.*?-rf\s+).+/": {
        "severity": "CRITICAL",
        "reason": "Recursive force deletion of directory",
        "example": "rm -rf /path/to/dir"
    },
    r"\brm\s+(-[rf]+\s+|.*?-rf\s+)": {
        "severity": "CRITICAL",
        "reason": "Force deletion without confirmation",
        "example": "rm -rf file"
    },

    # Database destruction
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b": {
        "severity": "CRITICAL",
        "reason": "Drops database table/schema",
        "example": "DROP TABLE users"
    },
    r"\bTRUNCATE\s+(TABLE\s+)?\w+": {
        "severity": "HIGH",
        "reason": "Removes all data from table",
        "example": "TRUNCATE TABLE users"
    },
    r"\bDELETE\s+FROM\s+\w+\s*;?\s*$": {
        "severity": "CRITICAL",
        "reason": "DELETE without WHERE clause removes all rows",
        "example": "DELETE FROM users"
    },

    # Git force operations
    r"\bgit\s+push\s+.*--force\b": {
        "severity": "HIGH",
        "reason": "Force push rewrites history",
        "example": "git push --force origin main"
    },
    r"\bgit\s+push\s+.*-f\b": {
        "severity": "HIGH",
        "reason": "Force push (short form) rewrites history",
        "example": "git push -f origin main"
    },

    # System destruction
    r"\b(>\s*/dev/sd[a-z]|dd\s+if=.*of=/dev/sd[a-z])": {
        "severity": "CRITICAL",
        "reason": "Direct disk write (data destruction)",
        "example": "dd if=/dev/zero of=/dev/sda"
    },
    r"\bmkfs\.(ext[234]|xfs|btrfs)\s+/dev/sd[a-z]": {
        "severity": "CRITICAL",
        "reason": "Formats disk (destroys all data)",
        "example": "mkfs.ext4 /dev/sda1"
    },

    # Privilege escalation
    r"\bsudo\s+chmod\s+[0-7]{3,4}\s+/": {
        "severity": "HIGH",
        "reason": "Changing root permissions",
        "example": "sudo chmod 777 /"
    },
    r"\bsudo\s+rm\s+": {
        "severity": "HIGH",
        "reason": "Deletion with elevated privileges",
        "example": "sudo rm -rf /system"
    },

    # Network attacks
    r"\b(nmap|masscan)\s+.*--script\s+(http-slowloris|syn-flood)": {
        "severity": "CRITICAL",
        "reason": "Network attack scripts",
        "example": "nmap --script http-slowloris target"
    },

    # Kubernetes destruction
    r"\bkubectl\s+delete\s+.*--all\b": {
        "severity": "CRITICAL",
        "reason": "Deletes all resources in namespace",
        "example": "kubectl delete all --all"
    },
    r"\bkubectl\s+delete\s+namespace\s+\w+": {
        "severity": "HIGH",
        "reason": "Deletes entire namespace",
        "example": "kubectl delete namespace production"
    },

    # Docker destruction
    r"\bdocker\s+(system|container)\s+prune\s+.*--force\b": {
        "severity": "HIGH",
        "reason": "Force removal of Docker resources",
        "example": "docker system prune --force"
    },

    # AWS destruction
    r"\baws\s+s3\s+rb\s+.*--force\b": {
        "severity": "CRITICAL",
        "reason": "Force deletion of S3 bucket",
        "example": "aws s3 rb s3://bucket --force"
    },
    r"\baws\s+ec2\s+terminate-instances\b": {
        "severity": "HIGH",
        "reason": "Terminates EC2 instances",
        "example": "aws ec2 terminate-instances --instance-ids i-123"
    },
}

# Whitelist patterns (safe commands)
WHITELIST_PATTERNS = [
    r"^rm\s+-rf\s+/tmp/",  # Safe to delete temp files
    r"^rm\s+-rf\s+.*\.log$",  # Safe to delete log files
    r"^rm\s+-rf\s+.*node_modules",  # Safe to delete node_modules
    r"^git\s+push\s+.*--force-with-lease",  # Safer force push
]


def log_blocked_command(command: str, reason: str, severity: str, example: str) -> None:
    """Log blocked command to file."""
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()

    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "severity": severity,
        "example": example,
        "project_path": project_path
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def is_whitelisted(command: str) -> bool:
    """Check if command matches whitelist."""
    for pattern in WHITELIST_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def check_command(command: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Check command against dangerous patterns.
    Returns (severity, reason, example, pattern) if dangerous, None if safe.
    """
    # First check whitelist
    if is_whitelisted(command):
        return None

    # Check against dangerous patterns
    for pattern, info in DANGEROUS_PATTERNS.items():
        if re.search(pattern, command, re.IGNORECASE):
            return (
                info["severity"],
                info["reason"],
                info["example"],
                pattern
            )

    return None


def format_block_message(command: str, severity: str, reason: str, example: str) -> str:
    """Format user-friendly block message."""
    severity_emoji = {
        "CRITICAL": "🚨",
        "HIGH": "⚠️",
        "MEDIUM": "⚡"
    }

    emoji = severity_emoji.get(severity, "⚠️")

    return f"""
{emoji} **BLOCKED: Dangerous Command Detected**

**Severity**: {severity}
**Command**: `{command}`
**Reason**: {reason}

**Why this is dangerous**:
This command can cause irreversible data loss or system damage.

**Example of safe alternative**:
- Instead of `{example}`
- Consider safer alternatives or add explicit safeguards

**What to do**:
1. Review if this command is really necessary
2. Consider using a safer alternative
3. If you must proceed, ask your human to run it manually
4. Check `~/.claude/hooks/blocked.log` for details

🛡️ **This hook protects you from accidental data loss**
"""


def main():
    """Main hook entry point."""
    # Read tool use request from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract tool name and input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check bash commands
    if tool_name != "bash":
        # Allow all non-bash tools
        output = {
            "hookSpecificResponse": {
                "continue": True
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Extract command
    command = tool_input.get("command", "")

    if not command:
        # Allow empty commands
        output = {
            "hookSpecificResponse": {
                "continue": True
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Check if command is dangerous
    result = check_command(command)

    if result:
        severity, reason, example, pattern = result

        # Log the blocked attempt
        log_blocked_command(command, reason, severity, example)

        # Block execution
        block_message = format_block_message(command, severity, reason, example)

        output = {
            "hookSpecificResponse": {
                "continue": False,
                "reason": block_message
            }
        }

        print(json.dumps(output))
        sys.exit(0)
    else:
        # Allow safe commands
        output = {
            "hookSpecificResponse": {
                "continue": True
            }
        }
        print(json.dumps(output))
        sys.exit(0)


if __name__ == "__main__":
    main()
