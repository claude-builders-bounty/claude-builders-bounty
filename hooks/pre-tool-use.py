#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks dangerous bash commands."""

import json
import sys
import re
import os
from datetime import datetime, timezone

DANGEROUS_PATTERNS = [
    (
        re.compile(r"rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|.*-rf|.*--no-preserve-root)", re.IGNORECASE),
        "Recursive/forced file deletion (rm -rf or --no-preserve-root)",
    ),
    (
        re.compile(r"DROP\s+TABLE", re.IGNORECASE),
        "SQL DROP TABLE — destroys database tables",
    ),
    (
        re.compile(r"git\s+push\s+.*--force|git\s+push\s+.*-f\b", re.IGNORECASE),
        "Force push — rewrites remote git history",
    ),
    (
        re.compile(r"TRUNCATE\s+", re.IGNORECASE),
        "SQL TRUNCATE — deletes all rows from a table",
    ),
    (
        re.compile(r"DELETE\s+FROM\s+(?!.*\bWHERE\b)", re.IGNORECASE),
        "SQL DELETE FROM without WHERE clause — deletes all rows",
    ),
]

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command: str, reason: str, project_path: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project_path} | reason={reason} | command={command}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Return (is_dangerous, reason) for a bash command."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    is_dangerous, reason = check_command(command)
    if not is_dangerous:
        sys.exit(0)

    project_path = os.getcwd()
    log_blocked(command, reason, project_path)

    # stdout is shown to Claude as the blocking explanation
    print(f"🚫 BLOCKED: {reason}")
    print(f"   Command: {command}")
    print(f"   This command was blocked by the pre-tool-use safety hook.")
    print(f"   If you believe this is a false positive, ask the user to run it manually.")
    sys.exit(1)


if __name__ == "__main__":
    main()
