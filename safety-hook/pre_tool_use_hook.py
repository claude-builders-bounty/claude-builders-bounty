#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Interceptor

Blocks dangerous bash commands before execution.
Follows Claude Code hooks format: https://docs.anthropic.com/claude-code/hooks

Installation (2 commands):
1. mkdir -p ~/.claude/hooks && cp pre_tool_use_hook.py ~/.claude/hooks/
2. chmod +x ~/.claude/hooks/pre_tool_use_hook.py

Blocked patterns:
- rm -rf, rm -f (recursive/force delete)
- DROP TABLE, TRUNCATE (SQL destruction)
- git push --force (force push)
- DELETE FROM without WHERE clause
- chmod 777 (overly permissive)
- mkfs, dd if=/dev/zero (disk destruction)
"""

import sys
import json
import os
import re
import logging
from datetime import datetime, timezone

# === Configuration ===
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
PROJECT_PATH = os.getcwd()

# Destructive patterns and their explanations
BLOCKED_PATTERNS = [
    # File/Directory destruction
    {
        "pattern": r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b',
        "reason": "Blocked: `rm -rf` detected — recursive force delete can permanently remove files/directories",
        "severity": "critical",
    },
    {
        "pattern": r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b',
        "reason": "Blocked: `rm -fr` detected — force recursive delete can permanently remove files/directories",
        "severity": "critical",
    },
    {
        "pattern": r'\brm\s+-f\s+/\b',
        "reason": "Blocked: `rm -f /...` detected — forced deletion under root path",
        "severity": "critical",
    },
    {
        "pattern": r'\brm\s+(-[a-zA-Z]+\s+)?~/\b',
        "reason": "Blocked: `rm ~...` detected — deletion in home directory",
        "severity": "critical",
    },
    {
        "pattern": r'\brm\s+-rf\s+/\s*$',
        "reason": "Blocked: `rm -rf /` detected — SYSTEM DESTRUCTION COMMAND",
        "severity": "critical",
    },

    # SQL destruction
    {
        "pattern": r'\bDROP\s+TABLE\b',
        "reason": "Blocked: `DROP TABLE` detected — will permanently delete database table",
        "severity": "critical",
    },
    {
        "pattern": r'\bTRUNCATE\s+(TABLE\s+)?\w+',
        "reason": "Blocked: `TRUNCATE` detected — will delete all rows from table without logging",
        "severity": "critical",
    },
    {
        "pattern": r'\bDELETE\s+FROM\s+\w+(?!.*\bWHERE\b)',
        "reason": "Blocked: `DELETE FROM` without WHERE clause — will delete ALL rows from table",
        "severity": "critical",
    },

    # Git force push
    {
        "pattern": r'\bgit\s+push\s+.*--force\b',
        "reason": "Blocked: `git push --force` detected — will overwrite remote history",
        "severity": "high",
    },
    {
        "pattern": r'\bgit\s+push\s+.*-f\b',
        "reason": "Blocked: `git push -f` detected — will overwrite remote history",
        "severity": "high",
    },
    {
        "pattern": r'\bgit\s+push\s+--force-with-lease\b',
        "reason": "Blocked: `git push --force-with-lease` detected — force push variant",
        "severity": "high",
    },

    # Overly permissive
    {
        "pattern": r'\bchmod\s+777\b',
        "reason": "Blocked: `chmod 777` detected — grants full access to all users (security risk)",
        "severity": "high",
    },
    {
        "pattern": r'\bchmod\s+-R\s+777\b',
        "reason": "Blocked: `chmod -R 777` detected — recursive full access (critical security risk)",
        "severity": "critical",
    },

    # Disk destruction
    {
        "pattern": r'\bmkfs\b',
        "reason": "Blocked: `mkfs` detected — will format/destroy filesystem",
        "severity": "critical",
    },
    {
        "pattern": r'\bdd\s+if=/dev/zero\b',
        "reason": "Blocked: `dd if=/dev/zero` detected — will overwrite disk with zeros",
        "severity": "critical",
    },
    {
        "pattern": r'\bdd\s+if=/dev/null\b',
        "reason": "Blocked: `dd if=/dev/null` detected — will overwrite disk",
        "severity": "critical",
    },

    # Process/system
    {
        "pattern": r'\bkill\s+-9\s+-1\b',
        "reason": "Blocked: `kill -9 -1` detected — will kill all user processes",
        "severity": "critical",
    },
    {
        "pattern": r'\b:\(\)\{\s*:\|:\s*&\s*\}\s*;:',
        "reason": "Blocked: Fork bomb detected — will crash the system",
        "severity": "critical",
    },

    # Network/data exfil
    {
        "pattern": r'\bcurl\s+.*\|.*bash\b',
        "reason": "Blocked: `curl ... | bash` detected — piping remote script to shell (security risk)",
        "severity": "high",
    },
    {
        "pattern": r'\bwget\s+.*-O-\s*\|.*sh\b',
        "reason": "Blocked: `wget ... | sh` detected — piping remote script to shell (security risk)",
        "severity": "high",
    },
]


def setup_logging():
    """Set up logging to file"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def read_input():
    """Read JSON input from stdin (Claude Code hooks format)"""
    try:
        raw = sys.stdin.read()
        if not raw:
            return None
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return None


def check_command(tool_name, input_data):
    """Check if command matches any blocked pattern"""
    if tool_name != "bash":
        return None

    command = ""
    if isinstance(input_data, dict):
        command = input_data.get("command", "") or input_data.get("content", "")
    elif isinstance(input_data, str):
        command = input_data

    if not command:
        return None

    for rule in BLOCKED_PATTERNS:
        if re.search(rule["pattern"], command, re.IGNORECASE | re.MULTILINE):
            return {
                "blocked": True,
                "reason": rule["reason"],
                "severity": rule["severity"],
                "command": command[:200],
            }

    return None


def main():
    """Main hook entry point"""
    setup_logging()

    # Read input from stdin
    input_data = read_input()
    if input_data is None:
        # No input or invalid — allow (don't break normal operation)
        sys.exit(0)

    # Extract tool name and command
    tool_name = input_data.get("tool", "")
    command_input = input_data

    # Check against blocked patterns
    result = check_command(tool_name, command_input)

    if result and result["blocked"]:
        # Log the blocked attempt
        logging.warning(
            f"BLOCKED [{result['severity']}] | cmd='{result['command']}' | path={PROJECT_PATH}"
        )

        # Output block response (Claude Code hooks format)
        output = {
            "type": "block",
            "reason": result["reason"],
            "severity": result["severity"],
            "blocked_command": result["command"][:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "suggestion": "If you need to run this command, consider using a safer alternative or run it manually with explicit confirmation.",
        }
        print(json.dumps(output, indent=2))
        sys.exit(1)  # Exit with error to block execution
    else:
        # Allow — no match found
        sys.exit(0)


if __name__ == "__main__":
    main()
