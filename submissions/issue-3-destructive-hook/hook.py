#!/usr/bin/env python3
"""
Pre-tool-use hook: blocks destructive bash and SQL commands.

Intercepts Claude Code tool calls before execution. If a dangerous command
is detected, exits with code 2 (block) and writes a reason to stdout so
Claude receives it. Every blocked attempt is logged to ~/.claude/hooks/blocked.log.

Usage:
    Place in ~/.claude/hooks/pre-tool-use.d/block-destructive.py
    Make executable: chmod +x ~/.claude/hooks/pre-tool-use.d/block-destructive.py

Hook input (stdin, JSON):
    {
      "tool_name": "Bash",
      "tool_input": {"command": "..."}
    }

Exit codes:
    0  — allow (do nothing)
    2  — block (stdout is shown to Claude as the reason)
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Each entry: (pattern, human-readable reason)
BLOCKED_PATTERNS: list[tuple[str, str]] = [
    # rm -rf (any variant: rm -rf, rm -fr, rm -Rf, rm -rRf, etc.)
    (r"\brm\s+(-\S*[rR]\S*f\S*|-\S*f\S*[rR]\S*)\s", "rm -rf destroys files recursively and irreversibly"),
    # DROP TABLE / DROP DATABASE / DROP SCHEMA
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "DROP TABLE/DATABASE/SCHEMA permanently deletes data"),
    # git push --force / git push -f  (but NOT --force-with-lease which is safe)
    (r"\bgit\s+push\b.*\s(--force(?!-with-lease)|-f)\b", "git push --force rewrites remote history and can destroy teammates' work"),
    # TRUNCATE TABLE (no safe context)
    (r"\bTRUNCATE\s+(TABLE\s+)?\w", "TRUNCATE immediately deletes all rows without a WHERE clause"),
    # DELETE FROM without WHERE clause (no WHERE anywhere in the statement)
    (r"\bDELETE\s+FROM\s+\S+\s*(?:;|$)", "DELETE FROM without a WHERE clause deletes every row in the table"),
]

COMPILED = [(re.compile(pat, re.IGNORECASE | re.MULTILINE), reason) for pat, reason in BLOCKED_PATTERNS]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked attempt to the log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  project : {project_path}\n"
        f"  reason  : {reason}\n"
        f"  command : {command!r}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def check_command(command: str) -> tuple[bool, str]:
    """Return (is_blocked, reason). Checks every pattern."""
    for pattern, reason in COMPILED:
        if pattern.search(command):
            return True, reason
    return False, ""


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Unparseable input — let it through
        sys.exit(0)

    tool_name: str = payload.get("tool_name", "")
    tool_input: dict = payload.get("tool_input", {})

    # Only inspect Bash tool calls
    if tool_name.lower() not in ("bash", "execute_bash"):
        sys.exit(0)

    command: str = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)
    if not blocked:
        sys.exit(0)

    # Determine project path
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # Log the attempt
    log_blocked(command, reason, project_path)

    # Tell Claude why it was blocked
    print(
        f"BLOCKED: {reason}\n"
        f"\n"
        f"The command you attempted has been blocked by the safety hook.\n"
        f"Attempted: {command!r}\n"
        f"\n"
        f"Consider a safer alternative:\n"
        f"  - For file deletion: move to trash or use `rm` without -rf\n"
        f"  - For SQL deletes: add a WHERE clause\n"
        f"  - For git force push: use --force-with-lease instead\n"
        f"  - For DROP: create a backup first (pg_dump / mysqldump)\n"
        f"\n"
        f"This block has been logged to: {LOG_FILE}"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
