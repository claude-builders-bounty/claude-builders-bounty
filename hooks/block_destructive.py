#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Install: see README.md
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    (r'rm\s+(-\S*r\S*f\S*|-\S*f\S*r\S*|--recursive\b.*--force\b|--force\b.*--recursive\b)\s', "Recursive force delete (rm -rf)"),
    (r'\bDROP\s+TABLE\b', "SQL DROP TABLE — destroys table and all data"),
    (r'\bgit\s+push\s+(--force|-f)\b', "Force push — rewrites remote history"),
    (r'\bTRUNCATE\b', "SQL TRUNCATE — removes all table rows"),
    (r'\bDELETE\s+FROM\s+\w[\w.]*\s*(?:;|$)', "DELETE without WHERE clause — deletes all rows"),
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _log(command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().isoformat()} | BLOCKED | {reason} | "
            f"cwd={os.getcwd()} | cmd={command!r}\n"
        )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if data.get("tool") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            _log(command, reason)
            print(json.dumps({
                "decision": "block",
                "reason": (
                    f"🚫 Blocked: {reason}\n"
                    f"Command: {command!r}\n"
                    f"Logged to: {LOG_PATH}\n\n"
                    "If this was intentional, run the command directly in your terminal."
                ),
            }))
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
