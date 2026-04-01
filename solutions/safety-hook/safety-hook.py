#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Install: cp safety-hook.py ~/.claude/hooks/pre-tool-use.py
"""
import json
import sys
import re
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Blocked patterns: (compiled_regex, description)
BLOCKED_PATTERNS = []

def _add(pattern, desc, flags=re.IGNORECASE | re.MULTILINE):
    BLOCKED_PATTERNS.append((re.compile(pattern, flags), desc))

# rm -rf / rm -r -f (recursive + force together)
_add(r"\brm\s+-(\w*r\w*f|\w*f\w*r)\b", "rm -rf (recursive force delete)")
_add(r"\brm\s+-\w*r\w*\s+-\w*f|\brm\s+-\w*f\w*\s+-\w*r", "rm with -r and -f flags")

# SQL destructive operations (not inside quotes)
_add(r"^\s*(DROP\s+(TABLE|DATABASE|SCHEMA|INDEX))", "DROP TABLE/DATABASE")
_add(r"^\s*TRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE TABLE")
_add(r"^\s*DELETE\s+FROM\s+\w+\s*;?\s*$", "DELETE FROM without WHERE clause")

# Git force push
_add(r"\bgit\s+push\s+.*--force\b", "git push --force")
_add(r"\bgit\s+push\s+-[\w]*f", "git push -f")

# Filesystem destruction
_add(r"\bmkfs\b", "mkfs (format filesystem)")
_add(r"\bdd\s+.*of=/dev/", "dd writing to device")
_add(r">\s*/dev/sd[a-z]", "redirect to block device")

# Dangerous permissions
_add(r"\bchmod\s+(-R\s+)?777\s+/", "chmod 777 on root paths")
_add(r"\bchown\s+-R\s+.*\s+/", "recursive chown on root")

# Fork bomb
_add(r":\(\)\{", "fork bomb")

# sudo rm (any rm with sudo)
_add(r"\bsudo\s+rm\b", "sudo rm")

# System shutdown
_add(r"\b(shutdown|poweroff|halt)\s", "system shutdown")
_add(r"^\s*reboot\s*$", "system reboot")


def check_command(command: str) -> tuple:
    """Check if a command matches any blocked pattern."""
    for pattern, description in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, description
    return False, ""


def log_blocked(command: str, reason: str):
    """Log blocked attempt with timestamp."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = json.dumps({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": command[:500],
        "reason": reason,
        "action": "BLOCKED"
    })
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def main():
    """Pre-tool-use hook entry point.
    
    Reads a JSON event from stdin with tool_name and tool_input.
    Exits 0 to allow, non-zero to block.
    """
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    if tool_name not in ("bash", "shell", "terminal", "execute", "run"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, reason)
        print(json.dumps({
            "error": f"\U0001f6d1 BLOCKED: {reason}",
            "message": f"Command blocked by safety hook: {reason}. "
                       f"Review and modify the command before retrying.",
            "blocked_command": command[:200]
        }))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
