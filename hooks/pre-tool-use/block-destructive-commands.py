#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before execution and blocks them.
Follows the Claude Code hooks format for ~/.claude/hooks/

Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --- Configuration ---

# Each pattern: (compiled_regex, key, description)
BLOCKED_PATTERNS: list[tuple] = [
    # rm -rf variants (must come before generic rm checks)
    (
        r'\brm\s+.*(-(?:\w*[rR]\w*[fF]\w*|[fF]\w*[rR]\w*))\b',
        "rm_rf",
        "Recursive force delete (rm -rf) — can destroy entire directories",
    ),
    # git push --force / -f variants
    (
        r'\bgit\s+push\s+.*(--force\b|-[a-zA-Z]*f\b)',
        "git_force",
        "git push --force — can overwrite remote history",
    ),
    # DROP TABLE (SQL)
    (
        r'\bDROP\s+TABLE\b',
        "drop_table",
        "DROP TABLE — will permanently delete a database table",
    ),
    # TRUNCATE (SQL)
    (
        r'\bTRUNCATE\b',
        "truncate",
        "TRUNCATE — will permanently empty a database table",
    ),
    # DELETE FROM without WHERE clause
    (
        r'\bDELETE\s+FROM\s+\S+(?:\s+WHERE\b)?\s*;?\s*$',
        "delete_no_where",
        "DELETE FROM without WHERE — will delete all rows in a table",
    ),
]

# Compile all patterns
COMPILED_PATTERNS = [
    (re.compile(p, re.IGNORECASE), key, desc)
    for p, key, desc in BLOCKED_PATTERNS
]

# Log file path
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


def classify_command(command: str) -> Optional[tuple[str, str]]:
    """Check if a command matches any blocked pattern.
    Returns (key, description) tuple or None if safe."""
    for pattern, key, desc in COMPILED_PATTERNS:
        if pattern.search(command):
            return key, desc
    return None


def log_blocked(command: str, reason: str, project_path: str = "") -> None:
    """Log a blocked attempt to the log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = json.dumps({
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "project_path": project_path,
    }, ensure_ascii=False)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def main():
    """Main hook entry point. Reads Claude Code hook input from stdin."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check against blocked patterns
    result = classify_command(command)

    if result:
        key, description = result
        project_path = hook_input.get("project_path", os.getcwd())

        # Log the blocked attempt
        log_blocked(command, description, project_path)

        # Output blocking message (Claude Code reads stderr for hook messages)
        message = (
            f"BLOCKED: {description}\n"
            f"Command: {command}\n"
            f"This command was intercepted by the pre-tool-use safety hook.\n"
            f"If you are sure this is safe, you can modify the hook configuration.\n"
            f"Logged to: {LOG_FILE}"
        )
        print(message, file=sys.stderr)

        # Exit with code 2 to signal Claude Code to block the command
        sys.exit(2)

    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
