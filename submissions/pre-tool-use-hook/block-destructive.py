#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook.
Blocks dangerous bash commands before they execute.

Install: cp this file to ~/.claude/hooks/pre-tool-use/block-destructive
"""

import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
LOG_DIR = os.path.dirname(LOG_FILE)

# ── Dangerous patterns ──────────────────────────────────────────
# Each entry: (regex, reason)
DANGEROUS_PATTERNS = [
    # File destruction
    (r'\brm\s+(-rf|--recursive\s+--force|-r\s*-f|-f\s*-r)\b', 'Recursive force delete'),
    (r'\brm\s+(-fr|-rf)\s+/', 'Delete root filesystem'),
    (r'\brm\s+(-rf|--recursive\s+--force)\s+~?\s*$', 'Delete without path'),

    # Database destruction
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'Destructive DDL statement'),
    (r'\bTRUNCATE\b', 'Destructive DML statement'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE without WHERE clause'),

    # Git force push
    (r'\bgit\s+push\s+.*--force\b', 'Force push to git remote'),
    (r'\bgit\s+push\s+.*\-f\s', 'Force push to git remote'),

    # Bulk operations
    (r'\bchmod\s+-R\s+0+[0-7]*\s+', 'Recursive permission removal'),
    (r'\bchown\s+-R\s+.*:', 'Recursive ownership change (high risk)'),
    (r'\bdd\s+if=.*\s+of=', 'Raw disk write'),

    # Pipe to shell (common exploit pattern)
    (r'\bcurl\s+.*\s*\|\s*(bash|sh)\b', 'Pipe network download to shell'),
    (r'\bwget\s+.*\s*-O-\s*\|\s*(bash|sh)\b', 'Pipe network download to shell'),
]


def load_blocked_count():
    """Read the number of blocked attempts (used for the message)."""
    count = 0
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE) as f:
                for _ in f:
                    count += 1
    except OSError:
        pass
    return count


def log_blocked(command: str, reason: str):
    """Log the blocked attempt to the log file."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] BLOCKED | reason={reason} | cmd={command}\n")
    except OSError:
        pass


def main():
    stdin_data = sys.stdin.read()
    if not stdin_data.strip():
        # No stdin data — allow
        sys.exit(0)

    try:
        tool_call = json.loads(stdin_data)
    except json.JSONDecodeError:
        # Not JSON — allow it through (could be a different tool)
        sys.exit(0)

    # Only intercept Bash tool calls
    tool_name = tool_call.get('tool', {}).get('name', '')
    if tool_name not in ('Bash', 'bash'):
        sys.exit(0)

    command = tool_call.get('tool', {}).get('input', {}).get('command', '')
    if not command:
        sys.exit(0)

    # Check against dangerous patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Get project context
            project_path = os.getcwd()
            blocked_count = load_blocked_count() + 1

            log_blocked(command, reason)

            # Write block message to stderr — Claude Code displays this
            print(
                f"\n🚫 BLOCKED ({blocked_count}) — {reason}",
                file=sys.stderr,
            )
            print(
                f"   Command: {command[:200]}",
                file=sys.stderr,
            )
            print(
                f"   Project: {project_path}",
                file=sys.stderr,
            )
            print(
                f"\n   This command was blocked by the pre-tool-use hook.",
                file=sys.stderr,
            )
            print(
                f"   To proceed, manually run it in your terminal.",
                file=sys.stderr,
            )
            print(
                f"   Logged to: {LOG_FILE}",
                file=sys.stderr,
            )

            sys.exit(1)

    # Command is safe
    sys.exit(0)


if __name__ == '__main__':
    main()
