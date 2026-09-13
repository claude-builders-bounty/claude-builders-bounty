#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook
Blocks destructive bash commands before execution and logs blocked attempts to ~/.claude/hooks/blocked.log.
"""

import sys
import os
import json
import re
from datetime import datetime, timezone

LOG_FILE_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns to block
BLOCKED_PATTERNS = [
    (
        r'\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\b|\brm\s+.*--(recursive|force)\b',
        "Recursive force removal (rm -rf)"
    ),
    (
        r'\bDROP\s+TABLE\b',
        "Destructive SQL DROP TABLE command"
    ),
    (
        r'\bgit\s+push\s+.*(--force|-f|--force-with-lease)\b',
        "Forced git push operation"
    ),
    (
        r'\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_"`\.]+\b',
        "Destructive SQL TRUNCATE command"
    ),
]

def is_delete_from_without_where(command: str) -> bool:
    """Checks if command contains a DELETE FROM statement without a WHERE clause."""
    # Match DELETE FROM <table> ... until end of statement or semicolon
    statements = command.split(';')
    for stmt in statements:
        stmt_strip = stmt.strip()
        if re.search(r'\bDELETE\s+FROM\b', stmt_strip, re.IGNORECASE):
            if not re.search(r'\bWHERE\b', stmt_strip, re.IGNORECASE):
                return True
    return False

def check_command(command: str) -> tuple[bool, str]:
    """
    Evaluates command against security rules.
    Returns (is_blocked, reason).
    """
    if not command:
        return False, ""

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason

    if is_delete_from_without_where(command):
        return True, "SQL DELETE FROM statement missing a WHERE clause"

    return False, ""

def log_blocked_attempt(command: str, project_path: str, reason: str, log_path: str = LOG_FILE_PATH):
    """Logs blocked execution attempt to log_path in ISO 8601 format."""
    try:
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] BLOCKED | project='{project_path}' | reason='{reason}' | command='{command}'\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def main():
    command = ""
    project_path = os.getcwd()

    # Parse input from stdin (JSON payload from Claude Code hooks) or CLI arguments
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                if stdin_content.startswith("{"):
                    data = json.loads(stdin_content)
                    tool_input = data.get("tool_input", {})
                    if isinstance(tool_input, dict):
                        command = tool_input.get("command", "")
                    project_path = data.get("cwd", project_path) or project_path
                else:
                    command = stdin_content
        except Exception:
            pass

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked_attempt(command, project_path, reason)
        error_message = (
            f"\n🚨 [SECURITY HOOK BLOCKED COMMAND]\n"
            f"Reason: {reason}\n"
            f"Blocked Command: {command}\n"
            f"Project Path: {project_path}\n"
            f"Log Entry Saved To: {LOG_FILE_PATH}\n"
        )
        sys.stderr.write(error_message)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
