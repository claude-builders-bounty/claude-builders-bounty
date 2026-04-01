#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Install: ln -sf /path/to/this/hook.py ~/.claude/hooks/pre-tool-use-destructive-hook.py

Claude Code will call this before every tool use. If the bash command matches
a dangerous pattern, we exit non-zero to block the tool and print a message.
"""

import sys
import json
import re
import os
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    (r"rm\s+-rf\s+/(?:\S+)?", "rm -rf / — attempts to delete root filesystem"),
    (r"rm\s+-rf\s+\*", "rm -rf * — recursive delete from current directory"),
    (r"DROP\s+TABLE", "DROP TABLE — destructive SQL without WHERE clause"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE — destructive SQL, use DELETE with WHERE"),
    (r"git\s+push\s+--force", "git push --force — rewrites remote history"),
    (r"git\s+push\s+-f", "git push -f — rewrites remote history"),
    (r"DELETE\s+FROM\s+\w+\s*;?\s*$", "DELETE FROM without WHERE — deletes all rows"),
    (r"DELETE\s+FROM\s+\w+\s+WHERE\s+'1'='1'", "DELETE FROM WHERE 1=1 — deletes all rows"),
    (r"echo\s+['\"]\s*>\s*/", "echo redirect to system path — potential overwrite"),
    (r"chmod\s+-R\s+777", "chmod -R 777 — world-writable permissions"),
    (r":(){ :|:& };:", "Fork bomb — DoS via process spawning"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command: str, reason: str):
    """Append blocked attempt to log file."""
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    project = os.environ.get("CLAUDE_PROJECT_PATH", "unknown")
    entry = f"[{ts}] BLOCKED | project: {project} | reason: {reason} | command: {command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Check if command is dangerous. Returns (blocked, reason)."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        # Not JSON input, allow through
        sys.exit(0)

    # Extract bash commands from the payload
    tool_name = payload.get("name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = payload.get("input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason)
        print(f"""
⛔  HOOK BLOCKED — DANGEROUS COMMAND

The following pattern was detected and blocked:
  {reason}

Command attempted:
  {command[:200]}{'...' if len(command) > 200 else ''}

This command was blocked by your pre-tool-use safety hook.

If you need to proceed:
  1. Edit the hook (~/.claude/hooks/pre-tool-use-destructive-hook.py)
  2. Remove or modify the blocking pattern
  3. Restart Claude Code

To disable this hook temporarily:
  mv ~/.claude/hooks/pre-tool-use-destructive-hook.py ~/.claude/hooks/pre-tool-use-destructive-hook.py.disabled
""", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
