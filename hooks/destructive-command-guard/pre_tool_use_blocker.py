#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Guard
Intercepts and blocks dangerous destructive bash commands before execution.
Compliant with Claude Code hook specifications (~/.claude/hooks/).
"""

import sys
import json
import re
import os
from datetime import datetime, timezone

# Dangerous patterns to block
PATTERNS = [
    (
        r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f\b|-[a-zA-Z]*f[a-zA-Z]*r\b|--recursive\s+--force\b|--force\s+--recursive\b|-r\s+-f\b|-f\s+-r\b)",
        "Recursive and forced directory/file deletion ('rm -rf')",
    ),
    (
        r"(?i)\bDROP\s+TABLE\b",
        "Destructive SQL table deletion ('DROP TABLE')",
    ),
    (
        r"\bgit\s+push\s+.*(--force|-f\b|--force-with-lease\b)",
        "Destructive remote branch overwrite ('git push --force')",
    ),
    (
        r"(?i)\bTRUNCATE(\s+TABLE)?\s+[a-zA-Z0-9_`\"\[\]]+",
        "Destructive SQL table purge ('TRUNCATE TABLE')",
    ),
    (
        r"(?i)\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"\[\]]+(?!\s+WHERE\b)(\s*;|\s*$)",
        "Unbounded SQL record deletion without a WHERE clause ('DELETE FROM ...')",
    ),
]


def check_command(command: str) -> tuple[bool, str]:
    """Inspects a command string against known destructive patterns."""
    if not command:
        return False, ""

    # Normalize command string
    trimmed = command.strip()

    for pattern, description in PATTERNS:
        if re.search(pattern, trimmed):
            return True, description

    return False, ""


def log_blocked_attempt(command: str, project_path: str, reason: str):
    """Logs the blocked attempt to ~/.claude/hooks/blocked.log with ISO 8601 timestamp."""
    home_dir = os.path.expanduser("~")
    hooks_dir = os.path.join(home_dir, ".claude", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    log_file = os.path.join(hooks_dir, "blocked.log")

    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = (
        f"[{timestamp}] BLOCKED: {reason}\n"
        f"  Command: {command}\n"
        f"  Project Path: {project_path}\n"
    )

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def main():
    # Read payload from stdin or argument
    payload = {}
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
        try:
            payload = json.loads(raw_input)
        except json.JSONDecodeError:
            # Treat entire arg string as command
            payload = {"tool": "Bash", "tool_input": {"command": raw_input}}
    else:
        try:
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                payload = json.loads(stdin_data)
        except Exception:
            payload = {}

    tool_name = payload.get("tool", "") or payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or payload.get("input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
    project_path = payload.get("project_path", os.getcwd())

    # Only inspect Bash commands
    if tool_name and tool_name.lower() not in ("bash", "execute_command", "sh"):
        sys.exit(0)

    if not command and isinstance(payload, str):
        command = payload

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked_attempt(command, project_path, reason)
        error_msg = (
            f"\n[COMMAND BLOCKED BY PRE-TOOL-USE HOOK]\n"
            f"Reason: {reason}\n"
            f"Attempted Command: {command}\n"
            f"Action: Blocked to prevent catastrophic state or data loss.\n"
            f"Review logged at: ~/.claude/hooks/blocked.log\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)

    # Safe command
    sys.exit(0)


if __name__ == "__main__":
    main()
