#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Place at ~/.claude/hooks/pre-tool-use and make executable.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKED_PATTERNS = [
    # rm -rf (any variant with -rf or -fr flags)
    (r"\brm\s+(-[a-zA-Z]*[rf]|--recursive)\b", "rm -rf: recursive force delete"),
    # DROP TABLE
    (r"\bDROP\s+TABLE\b", "DROP TABLE: SQL table deletion"),
    # git push --force or -f
    (r"\bgit\s+push\s+.*(-f|--force)\b", "git push --force: force push"),
    # TRUNCATE
    (r"\bTRUNCATE\s+TABLE?\b", "TRUNCATE: SQL table truncation"),
    # DELETE FROM without WHERE
    (r"\bDELETE\s+FROM\b", "DELETE FROM without WHERE: unqualified SQL delete"),
]


def get_log_path() -> Path:
    """Return path to the blocked attempts log file."""
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "blocked.log"


def log_blocked(command: str, project_path: str) -> None:
    """Log a blocked attempt with timestamp, command, and project path."""
    log_path = get_log_path()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"{timestamp} | {project_path} | {command}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def is_destructive(command: str) -> tuple[bool, str]:
    """Check if a command matches any destructive pattern. Returns (is_blocked, reason)."""
    command_upper = command.upper()
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Special case: DELETE FROM without WHERE
            if "DELETE FROM" in command_upper:
                if "WHERE" not in command_upper:
                    return True, reason
                continue
            return True, reason
    
    return False, ""


def main() -> None:
    # Read the tool use request from stdin (Claude Code hook protocol)
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Allow on parse error

    # Only intercept bash tool
    if payload.get("tool_name") != "bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")
    project_path = payload.get("project_path", "")

    blocked, reason = is_destructive(command)
    if blocked:
        log_blocked(command, project_path)
        print(f"🛡️  BLOCKED: {reason}", file=sys.stderr)
        print(f"   Command: {command}", file=sys.stderr)
        print("   This destructive command was prevented for safety. Please use a safer alternative or confirm the operation is intentional.", file=sys.stderr)
        sys.exit(1)  # Block the tool use


if __name__ == "__main__":
    main()