#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook
Blocks destructive commands before execution in Claude Code.
Logs blocked attempts to ~/.claude/hooks/blocked.log.
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Log file path as specified in Acceptance Criteria
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# Forbidden patterns and explanation reasons
FORBIDDEN_PATTERNS = [
    (
        r"\brm\s+.*(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r|--recursive\s+--force|--force\s+--recursive)\b",
        "Destructive recursive deletion (`rm -rf`)"
    ),
    (
        r"\bDROP\s+TABLE\b",
        "Database drop table statement (`DROP TABLE`)"
    ),
    (
        r"\bgit\s+push\s+.*(-f\b|--force\b|--force-with-lease\b)",
        "Force-pushing git history (`git push --force`)"
    ),
    (
        r"\bTRUNCATE(\s+TABLE)?\b",
        "Database table truncation (`TRUNCATE`)"
    ),
    (
        r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b)",
        "Unbounded database deletion without a WHERE clause (`DELETE FROM ...`)"
    )
]

def log_blocked_command(command: str, project_path: str, reason: str):
    """Logs the blocked attempt with timestamp, command, and project path."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] BLOCKED: {command!r} | "
            f"Project: {project_path} | "
            f"Reason: {reason}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def check_command(command: str) -> tuple[bool, str]:
    """
    Checks if a command contains any forbidden destructive patterns.
    Returns (is_blocked, reason).
    """
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    # Read Claude Code hook input from stdin (JSON format)
    input_data = {}
    try:
        raw_stdin = sys.stdin.read()
        if raw_stdin.strip():
            input_data = json.loads(raw_stdin)
    except Exception:
        # Fallback if command was passed via arguments
        if len(sys.argv) > 1:
            input_data = {"tool": "Bash", "input": {"command": " ".join(sys.argv[1:])}}

    # Extract tool information
    tool_name = input_data.get("tool", "") or input_data.get("tool_name", "")
    tool_input = input_data.get("input", {}) or input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    project_path = input_data.get("project_path", os.getcwd())

    # Only inspect Bash / shell execution tools
    if command:
        is_blocked, reason = check_command(command)
        if is_blocked:
            log_blocked_command(command, project_path, reason)
            
            # Print a clear, formatted warning message to Claude
            rejection_message = (
                f"\n🚫 [SECURITY HOOK] Command execution blocked by pre-tool-use hook!\n"
                f"Attempted command : {command}\n"
                f"Reason            : {reason}\n"
                f"Logged to         : {LOG_FILE}\n\n"
                f"Dangerous actions like recursive deletion, force pushes, and unbounded SQL deletions "
                f"must be executed manually outside Claude Code for safety.\n"
            )
            sys.stderr.write(rejection_message)
            # Exit code 2 tells Claude Code that tool execution is denied
            sys.exit(2)

    # Allow command to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()
