#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands before execution.
Install: cp this file to ~/.claude/hooks/pre_tool_use.py
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",           # rm -rf / (root deletion)
    r"rm\s+-rf\s+\$",           # rm -rf $VAR (recursive variable expansion)
    r"DROP\s+TABLE",            # SQL DROP TABLE
    r"TRUNCATE\s+TABLE",        # SQL TRUNCATE
    r"DELETE\s+FROM\s+(?!.*WHERE)",  # DELETE FROM without WHERE
    r"git\s+push\s+--force",    # Force push
    r"git\s+push\s+-f",         # Force push alternative
    r":\(\)\{\s*:\|:;\}",       # Fork bomb
    r"curl.*\|.*sh",            # Pipe curl to shell (common install vector)
    r"wget.*\|.*sh",            # Pipe wget to shell
    r"shutdown\s+-h",           # System shutdown
    r"init\s+0",                # System halt
    r"mkfs\.",                  # Format filesystem
    r"dd\s+if=.*of=/dev/",      # Direct disk write
]

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

def log_blocked(tool: str, command: str):
    """Append blocked attempt to log file."""
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    project = os.environ.get("CLAUDE_PROJECT_PATH", "unknown")
    with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED {tool}: {command} | project: {project}\n")

def check_command(command: str):
    """
    Check if a command matches blocked patterns.
    Returns (blocked, message).
    """
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Command matches blocked pattern: {pattern}"
    return False, ""

def main():
    """Called by Claude Code with tool input on stdin."""
    import json
    try:
        tool_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # Pass through on parse error

    tool_name = tool_input.get("name", "")
    tool_args = tool_input.get("arguments", {})

    # Only check bash commands
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_args.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(tool_name, command)
        print(f"\nHOOK BLOCKED: {reason}", file=sys.stderr)
        print(f"The command '{command[:80]}...' matches a blocked pattern.", file=sys.stderr)
        print("This command would perform a potentially destructive action.", file=sys.stderr)
        print("If you need to run this, you can bypass the hook by confirming directly.", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
