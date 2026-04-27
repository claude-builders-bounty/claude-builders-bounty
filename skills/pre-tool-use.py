#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code.
Blocks dangerous bash commands before execution.
Place in ~/.claude/hooks/pre-tool-use

Claude Code passes: --tool TOOL_NAME --input JSON_INPUT
This hook checks the first argument (the command string) for dangerous patterns.
"""

import json
import os
import sys
from datetime import datetime

# Dangerous command patterns (case-insensitive regex)
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bDROP\s+TABLE\b',
    r'\bgit\s+push\s+--force\b',
    r'\bTRUNCATE\b',
    r'\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE\b)',
    r'\bformat\s+[A-Z]:\s*/fs:ntfs\b',
    r'\bsudo\s+rm\b',
    r'\bchmod\s+-R\s+777\b',
    r'\b:(){ :\|:& };:\b',  # Fork bomb
    r'\bdd\s+if=/dev/zero\b',
    r'\b>\/dev\/sda\b',
    r'\bmv\s+/\s+/dev/null\b',
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command: str, project_path: str):
    """Log blocked command attempt to file."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": command,
        "project_path": project_path,
        "reason": "matched_dangerous_pattern",
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(cmd: str) -> bool:
    """
    Check if a command matches any dangerous pattern.
    Returns True if blocked, False if allowed.
    """
    import re

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False


def main():
    # Claude Code passes tool name and JSON input
    if len(sys.argv) < 3:
        # Not a tool-use hook call; pass through
        sys.exit(0)

    tool_name = sys.argv[1]
    try:
        tool_input = json.loads(sys.argv[2])
    except (json.JSONDecodeError, IndexError):
        # Can't parse input; allow
        sys.exit(0)

    # Only check bash commands
    if tool_name not in ("bash", "execute_command", "shell_exec"):
        sys.exit(0)

    # Extract the command string
    command = (
        tool_input.get("command")
        or tool_input.get("cmd")
        or str(tool_input.get("input", ""))
    )

    if not command:
        sys.exit(0)

    if check_command(command):
        project_path = os.getcwd()
        log_blocked(command, project_path)

        # Print to stderr (Claude Code will capture this)
        print(
            f"\n⚠️  BLOCKED: Destructive command detected and prevented.\n"
            f"   Command: {command[:200]}\n"
            f"   Reason: Matched a dangerous security pattern.\n"
            f"   Tip: Use safer alternatives or confirm manually.\n"
            f"   Logged to: {LOG_FILE}",
            file=sys.stderr,
        )
        sys.exit(1)  # Non-zero exit blocks execution

    # Command is safe; allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
