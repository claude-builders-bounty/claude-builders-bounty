#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: blocks destructive bash commands.

Install:
  1. cp block_destructive.py ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py
  2. Add to ~/.claude/settings.json (see README.md)

Reads JSON from stdin, checks for dangerous patterns, returns deny/allow.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that indicate destructive commands.
# Each is a compiled regex applied to the command string.
BLOCKED_PATTERNS = [
    # Shell destructive
    re.compile(r'\brm\s+(-\S*\s+)*-\S*r\S*f\b'),         # rm -rf [flags] path
    re.compile(r'\brm\s+(-\S*\s+)*-\S*f\S*r\b'),         # rm -fr [flags] path
    re.compile(r'\bmkfs\b'),                                # format filesystem
    re.compile(r'\bdd\s+.*of=/dev/'),                       # dd to device

    # SQL destructive (only when the command itself is SQL-like, not inside strings)
    re.compile(r'^\s*(?:/\*.*\*/\s*)?(?:--\s*)?\bDROP\s+TABLE\b', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(?:/\*.*\*/\s*)?(?:--\s*)?\bTRUNCATE\s+(TABLE\s+)?\w+', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(?:/\*.*\*/\s*)?(?:--\s*)?\bDELETE\s+FROM\b(?!.*\bWHERE\b)', re.IGNORECASE | re.MULTILINE),

    # Git force push (block --force and -f, but allow --force-with-lease)
    re.compile(r'\bgit\s+push\b.*--force(?:\s|$|;)'),
    re.compile(r'\bgit\s+push\b[^;|&]*\s-f(?:\s|$|;)'),
]


def log_blocked(command: str, project_path: str) -> None:
    """Append blocked attempt to log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project_path} | command={command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked pattern. Returns (blocked, reason)."""
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, f"Blocked by hook: destructive command detected ({pattern.pattern})"
    return False, ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not JSON input — allow through
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, project_path)

        # Triple-signal output (signal A + B merged into one JSON object)
        output = {
            # Signal A: Claude Code hookSpecificOutput format
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
            # Signal B: legacy top-level format (for older Claude Code versions)
            "decision": "block",
            "reason": reason,
        }
        json.dump(output, sys.stdout)
        print()  # trailing newline

        # Signal C: reason to stderr + exit code 2
        print(reason, file=sys.stderr)
        sys.exit(2)

    # Not blocked — allow through (exit 0, silent)
    sys.exit(0)


if __name__ == "__main__":
    main()
