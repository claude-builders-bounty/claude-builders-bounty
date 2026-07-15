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
from enum import Enum
from functools import lru_cache


class Severity(str, Enum):
    """Severity levels for blocked commands"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Configuration
HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# Pre-create hooks directory
HOOKS_DIR.mkdir(parents=True, exist_ok=True)

# Dangerous patterns with pre-compiled regex
DANGEROUS_PATTERNS = [
    {
        "pattern": re.compile(r"rm\s+(-[rf]+\s+)*(/|~|\*|\.\.)", re.IGNORECASE),
        "reason": "Potentially destructive rm command targeting root, home, or parent directories",
        "severity": Severity.CRITICAL
    },
    {
        "pattern": re.compile(r"rm\s+-rf\s+", re.IGNORECASE),
        "reason": "Recursive force delete - extremely dangerous",
        "severity": Severity.CRITICAL
    },
    {
        "pattern": re.compile(r"DROP\s+TABLE\s+", re.IGNORECASE),
        "reason": "SQL DROP TABLE command - will delete entire table",
        "severity": Severity.CRITICAL
    },
    {
        "pattern": re.compile(r"TRUNCATE\s+", re.IGNORECASE),
        "reason": "SQL TRUNCATE command - will delete all data in table",
        "severity": Severity.CRITICAL
    },
    {
        "pattern": re.compile(r"DELETE\s+FROM\s+\w+\s*(;|WHERE\s+1\s*=|WHERE\s+true)", re.IGNORECASE),
        "reason": "SQL DELETE without proper WHERE clause - may delete all rows",
        "severity": Severity.CRITICAL
    },
    {
        "pattern": re.compile(r"git\s+push\s+(-f\b|--force)", re.IGNORECASE),
        "reason": "Force push can overwrite remote history and lose others' work",
        "severity": Severity.HIGH
    },
]


def log_blocked(command: str, reason: str, severity: Severity) -> None:
    """Log blocked attempt to blocked.log"""
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()

    log_entry = (
        f"[{timestamp}] [{severity}] {reason}\n"
        f"  Command: {command}\n"
        f"  Project: {project_path}\n"
        f"{'-' * 60}\n"
    )

    with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str, Severity]:
    """
    Check if command matches any dangerous pattern.
    Returns: (is_blocked, reason, severity)
    """
    for pattern_info in DANGEROUS_PATTERNS:
        if pattern_info["pattern"].search(command):
            return True, pattern_info["reason"], pattern_info["severity"]
    return False, "", Severity.LOW


def create_response(allow: bool, message: str, details: dict | None = None) -> dict:
    """Create standardized JSON response"""
    result = {"allow": allow, "message": message}
    if details:
        result["details"] = details
    return result


def main() -> int:
    """Main hook entry point"""
    # Read command from stdin or argument
    command = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()

    if not command:
        print(json.dumps(create_response(True, "No command provided")))
        return 0

    is_blocked, reason, severity = check_command(command)

    if is_blocked:
        log_blocked(command, reason, severity)
        result = create_response(
            allow=False,
            message=f"🚫 BLOCKED ({severity}): {reason}",
            details={
                "command": command,
                "reason": reason,
                "severity": severity.value,
                "logged_to": str(BLOCKED_LOG)
            }
        )
        print(json.dumps(result, indent=2))
        return 1

    # Command is safe
    result = create_response(True, "Command passed safety check")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
