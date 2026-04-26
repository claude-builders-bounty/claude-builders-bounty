#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands

Intercepts bash commands before execution and blocks dangerous patterns:
- rm -rf (recursive force delete)
- DROP TABLE / DROP DATABASE
- git push --force / git push -f
- TRUNCATE TABLE
- DELETE FROM without WHERE clause
- chmod 777 (world-writable permissions)
- mkfs / format (disk formatting)
- dd if= (raw disk write)
- > /dev/sda (direct device write)
- kill -9 -1 (kill all processes)

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Dangerous patterns — each has a regex, description, and severity
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS = [
    {
        "pattern": r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f|rm\s+.*-[a-zA-Z]*f[a-zA-Z]*r|\brm\s+-rf\b|\brm\s+-fr\b",
        "name": "rm -rf",
        "description": "Recursive force delete — can wipe entire directories",
        "severity": "critical",
    },
    {
        "pattern": r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b",
        "name": "DROP TABLE/DATABASE",
        "description": "Permanently deletes database objects",
        "severity": "critical",
    },
    {
        "pattern": r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b|\bgit\s+push\s+--force\b",
        "name": "git push --force",
        "description": "Force push overwrites remote history — can destroy others' work",
        "severity": "high",
    },
    {
        "pattern": r"\bTRUNCATE\s+(TABLE\s+)?\w+",
        "name": "TRUNCATE",
        "description": "Deletes all rows from a table without logging",
        "severity": "critical",
    },
    {
        "pattern": r"\bDELETE\s+FROM\s+\w+\s*(?!.*\bWHERE\b)(?:;|$|\n)",
        "name": "DELETE FROM without WHERE",
        "description": "Deletes all rows from a table — missing WHERE clause",
        "severity": "critical",
    },
    {
        "pattern": r"\bchmod\s+777\b",
        "name": "chmod 777",
        "description": "Sets world-readable/writable/executable permissions — security risk",
        "severity": "high",
    },
    {
        "pattern": r"\bmkfs\b|\bformat\s+[A-Z]:",
        "name": "mkfs / format",
        "description": "Formats a disk partition — irreversible data loss",
        "severity": "critical",
    },
    {
        "pattern": r"\bdd\s+if=",
        "name": "dd if=",
        "description": "Raw disk write — can overwrite entire drives",
        "severity": "critical",
    },
    {
        "pattern": r">\s*/dev/[a-z]",
        "name": "write to /dev/",
        "description": "Direct write to device file — can destroy disk",
        "severity": "critical",
    },
    {
        "pattern": r"\bkill\s+-9\s+-1\b",
        "name": "kill -9 -1",
        "description": "Kills ALL processes for the current user",
        "severity": "critical",
    },
    {
        "pattern": r"\bgit\s+reset\s+--hard\b",
        "name": "git reset --hard",
        "description": "Discards all uncommitted changes — cannot be undone",
        "severity": "high",
    },
    {
        "pattern": r"\bgit\s+clean\s+.*-[a-zA-Z]*f",
        "name": "git clean -f",
        "description": "Permanently deletes untracked files",
        "severity": "high",
    },
    {
        "pattern": r":\(\)\s*\{\s*:\|\:\s*&\s*\}\s*;",
        "name": "fork bomb",
        "description": "Fork bomb — crashes the system by spawning infinite processes",
        "severity": "critical",
    },
]

# ---------------------------------------------------------------------------
# Log file
# ---------------------------------------------------------------------------
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


def log_blocked(command: str, pattern_name: str, description: str, severity: str, project_path: str):
    """Log a blocked command attempt."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command[:500],  # Truncate very long commands
        "blocked_pattern": pattern_name,
        "description": description,
        "severity": severity,
        "project_path": project_path,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str) -> tuple[bool, dict | None]:
    """Check if a command matches any dangerous pattern.
    Returns (is_blocked, pattern_info)."""
    for p in DANGEROUS_PATTERNS:
        if re.search(p["pattern"], command, re.IGNORECASE | re.MULTILINE):
            return True, p
    return False, None


def main():
    """Main hook entry point. Reads tool input from stdin."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception):
        # If we can't parse input, allow the command (fail open)
        sys.exit(0)

    # Only check Bash tool calls
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    # Extract the command
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    # Check against dangerous patterns
    is_blocked, pattern = check_command(command)

    if is_blocked:
        # Get project path from environment or input
        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Log the blocked attempt
        log_blocked(command, pattern["name"], pattern["description"], pattern["severity"], project_path)

        # Output block message for Claude to see
        block_msg = (
            f"BLOCKED: {pattern['name']} detected.\n"
            f"Reason: {pattern['description']}\n"
            f"Severity: {pattern['severity'].upper()}\n"
            f"Command: {command[:200]}\n\n"
            f"This command was blocked by the safety hook to prevent accidental damage. "
            f"If you need to run this command, ask the user to execute it manually."
        )

        # Exit with non-zero to block the tool call
        print(block_msg, file=sys.stderr)
        sys.exit(2)

    # Command is safe — allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
