#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Guard Hook
====================================
Blocks dangerous bash commands before execution.
Compliant with Claude Code hooks format (~/.claude/hooks/).

Install:
  mkdir -p ~/.claude/hooks
  cp pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py
  chmod +x ~/.claude/hooks/pre_tool_use_guard.py

Usage:
  Receives JSON on stdin with the tool call details.
  Exits 0 to allow, 2 to block.
"""

import json
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# Dangerous patterns: (regex, friendly_name, severity)
BLOCKED_PATTERNS = [
    # Filesystem destruction
    (r'\brm\s+(-[^\s]*\s+)*-rf\s+/', 'Recursive force delete from root', 'CRITICAL'),
    (r'\brm\s+(-[^\s]*\s+)*-rf\s+~', 'Recursive force delete from home', 'CRITICAL'),
    (r'\brm\s+(-[^\s]*\s+)*-rf\s+\*', 'Recursive force delete with wildcard', 'CRITICAL'),
    (r'\brm\s+(-[^\s]*\s+)*-rf\s+\.', 'Recursive force delete current directory', 'HIGH'),
    (r'\brm\s+(-[^\s]*\s+)*-rf\s+/', 'Recursive force delete absolute path', 'CRITICAL'),
    # Database destruction
    (r'\bDROP\s+TABLE\b', 'DROP TABLE statement', 'CRITICAL'),
    (r'\bTRUNCATE\b', 'TRUNCATE statement', 'HIGH'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE without WHERE clause', 'HIGH'),
    # Git danger
    (r'\bgit\s+push\s+--force\b(?!-with-lease)', 'Force push (not using --force-with-lease)', 'HIGH'),
    (r'\bgit\s+reset\s+--hard\b', 'Hard reset (discards changes)', 'MEDIUM'),
    (r'\bgit\s+clean\s+-fd\b', 'Force clean (removes untracked)', 'MEDIUM'),
    # System commands
    (r'\bchmod\s+777\b', 'chmod 777 (insecure permissions)', 'MEDIUM'),
    (r'\bmkfs\b', 'Filesystem format command', 'CRITICAL'),
    (r'\bdd\s+if=.*of=/dev/', 'dd to block device', 'CRITICAL'),
    (r':\(\)\s*\{.*\}\s*;', 'Fork bomb detected', 'CRITICAL'),
    # Dangerous pipes
    (r'curl\s+.*\|\s*(ba)?sh', 'Piping curl output to shell', 'HIGH'),
    (r'wget\s+.*\|\s*(ba)?sh', 'Piping wget output to shell', 'HIGH'),
]

LOG_PATH = Path.home() / '.claude' / 'hooks' / 'blocked.log'


def log_blocked(command: str, pattern_name: str, severity: str):
    """Log blocked attempt with timestamp, command, and project path."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    project = os.getcwd()
    log_line = f"[{timestamp}] [{severity}] {pattern_name} | cmd: {command[:200]} | project: {project}\n"
    with open(LOG_PATH, 'a') as f:
        f.write(log_line)


def check_command(command: str) -> tuple[bool, str, str]:
    """Check command against blocked patterns. Returns (blocked, reason, severity)."""
    for pattern, name, severity in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
            return True, name, severity
    return False, '', ''


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Allow if we can't parse input

    # Extract the bash command from the tool call
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # Only check bash/exec tool calls
    if tool_name not in ('Bash', 'bash', 'exec', 'shell'):
        sys.exit(0)

    command = tool_input.get('command', '') or tool_input.get('input', '') or ''

    if not command:
        sys.exit(0)

    blocked, reason, severity = check_command(command)

    if blocked:
        log_blocked(command, reason, severity)

        # Output to stderr for Claude to see
        print(
            f"🚫 BLOCKED: This command was prevented by the safety hook.\n"
            f"   Reason: {reason}\n"
            f"   Severity: {severity}\n"
            f"   Command: {command[:120]}{'...' if len(command) > 120 else ''}\n"
            f"   If this is intentional, run it manually in your terminal.",
            file=sys.stderr,
        )
        sys.exit(2)  # Block the command
    else:
        sys.exit(0)  # Allow


if __name__ == '__main__':
    main()
