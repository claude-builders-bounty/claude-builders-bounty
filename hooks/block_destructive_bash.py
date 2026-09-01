#!/usr/bin/env python3
"""
PreToolUse Hook for Claude Code: Block Destructive Bash Commands
Acceptance Criteria:
- Intercepts dangerous bash commands before execution.
- Blocks:
  * rm -rf (including variants: rm -fr, rm -r -f, rm --recursive --force)
  * DROP TABLE (case-insensitive SQL)
  * git push --force (including -f, --force-with-lease, +refspec)
  * TRUNCATE (case-insensitive SQL)
  * DELETE FROM without WHERE clause
- Logs blocked attempts to ~/.claude/hooks/blocked.log with timestamp, attempted command, and project path.
- Returns clear explanation to Claude via stderr / JSON hook decision block.
- Zero interference with normal bash commands.
"""

import sys
import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Regex rules for dangerous command patterns
RULES = [
    (
        "rm_rf",
        re.compile(r'\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+-[a-zA-Z]*[rf][a-zA-Z]*|-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive)\b'),
        "Recursive force deletion ('rm -rf') is blocked to prevent accidental data loss."
    ),
    (
        "git_force_push",
        re.compile(r'\bgit(?:\s+-[cC]\s+\S+|\s+--\S+=\S+)*\s+push\s+.*?(?:--force\b|-f\b|--force-with-lease\b|\+[a-zA-Z0-9_/-]+:[a-zA-Z0-9_/-]+|\+[a-zA-Z0-9_/-]+\b)'),
        "Force push ('git push --force' / '-f' / '--force-with-lease') is blocked to protect remote git history."
    ),
    (
        "drop_table",
        re.compile(r'(?i)\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?["`\'\w.]+'),
        "Destructive database operation ('DROP TABLE') is blocked."
    ),
    (
        "truncate",
        re.compile(r'(?i)\bTRUNCATE\s+(?:TABLE\s+)?["`\'\w.]+'),
        "Destructive database operation ('TRUNCATE') is blocked."
    ),
]

DELETE_FROM_PATTERN = re.compile(r'(?i)\bDELETE\s+FROM\s+["`\'\w.]+')
WHERE_PATTERN = re.compile(r'(?i)\bWHERE\b')

def inspect_command(command: str) -> Optional[Tuple[str, str]]:
    """
    Analyzes a command string against destructive patterns.
    Returns (rule_name, reason) if blocked, otherwise None.
    """
    if not command or not isinstance(command, str):
        return None

    # Check direct regex rules
    for rule_name, pattern, reason in RULES:
        if pattern.search(command):
            return rule_name, reason

    # Check DELETE FROM without WHERE
    if DELETE_FROM_PATTERN.search(command):
        # Split statements by semicolon if multiple queries exist
        statements = command.split(";")
        for stmt in statements:
            if DELETE_FROM_PATTERN.search(stmt) and not WHERE_PATTERN.search(stmt):
                return "delete_without_where", "Unbounded database deletion ('DELETE FROM' without 'WHERE' clause) is blocked."

    return None

def log_blocked_attempt(command: str, cwd: str, reason: str):
    """
    Logs blocked attempts safely to ~/.claude/hooks/blocked.log
    """
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = (
            f"[{timestamp}] BLOCKED "
            f"| project: {cwd or os.getcwd()} "
            f"| command: {json.dumps(command)} "
            f"| reason: {reason}\n"
        )
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        # Non-blocking logging failure
        sys.stderr.write(f"Warning: Failed to write to {LOG_FILE}: {e}\n")

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        data = json.loads(raw_input)
    except Exception:
        # If input is not JSON or stdin is closed, exit cleanly
        sys.exit(0)

    tool_name = data.get("tool_name") or data.get("tool")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input") or data.get("input") or {}
    command = tool_input.get("command", "")
    cwd = data.get("cwd", "")

    blocked_info = inspect_command(command)
    if blocked_info:
        rule_name, reason = blocked_info
        log_blocked_attempt(command, cwd, reason)

        msg = f"🛑 COMMAND BLOCKED BY SECURITY POLICY:\n{reason}\nAttempted command: {command}"

        # Claude Code Hook JSON output protocol
        output = {
            "decision": "block",
            "reason": msg,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "additionalContext": msg
            }
        }
        print(json.dumps(output))
        sys.stderr.write(msg + "\n")
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
