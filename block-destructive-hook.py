#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous commands before execution and provides clear explanations.

Installation (2 commands):
  cp block-destructive-hook.py ~/.claude/hooks/pre-tool-use.py
  chmod +x ~/.claude/hooks/pre-tool-use.py

Usage:
  python3 block-destructive-hook.py "rm -rf /tmp"  # blocked
  python3 block-destructive-hook.py "echo hello"    # allowed
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import re

BLOCKED_PATTERNS = [
    {
        "name": "rm -rf",
        "pattern": r"\brm\s+-rf\b",
        "reason": "DANGEROUS: 'rm -rf' permanently deletes files/directories without confirmation.",
        "safe_alternative": "Use 'rm -i' for interactive deletion or 'find ... -delete' for safer batch removal."
    },
    {
        "name": "DROP TABLE",
        "pattern": r"\bDROP\s+TABLE\b",
        "reason": "DANGEROUS: 'DROP TABLE' permanently destroys a database table and all its data.",
        "safe_alternative": "Use 'ALTER TABLE' for schema changes, or backup before dropping."
    },
    {
        "name": "git push --force",
        "pattern": r"\bgit\s+push\s+--force\b",
        "reason": "DANGEROUS: 'git push --force' overwrites remote branch history and may destroy others' work.",
        "safe_alternative": "Use 'git push --force-with-lease' which is safer."
    },
    {
        "name": "TRUNCATE",
        "pattern": r"\bTRUNCATE\b",
        "reason": "DANGEROUS: 'TRUNCATE' instantly deletes ALL rows from a table with no rollback.",
        "safe_alternative": "Use 'DELETE FROM table_name WHERE condition' with specific filters."
    },
    {
        "name": "DELETE FROM without WHERE",
        "pattern": r"\bDELETE\s+FROM\s+\w+\s*$",
        "reason": "DANGEROUS: 'DELETE FROM table' without WHERE clause deletes ALL rows.",
        "safe_alternative": "Always include a WHERE clause to target specific rows."
    },
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def check_command(command: str) -> dict | None:
    normalized = " ".join(command.split())
    for entry in BLOCKED_PATTERNS:
        if re.search(entry["pattern"], normalized, re.IGNORECASE):
            return {
                "blocked": True,
                "command": command.strip(),
                "pattern_name": entry["name"],
                "reason": entry["reason"],
                "alternative": entry["safe_alternative"],
                "timestamp": datetime.now().isoformat(),
                "project_path": os.getcwd(),
            }
    return {"blocked": False}


def log_block(entry: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_line = (
        f"[{entry['timestamp']}] BLOCKED COMMAND\n"
        f"  Command: {entry['command']}\n"
        f"  Pattern: {entry['pattern_name']}\n"
        f"  Reason: {entry['reason']}\n"
        f"  Project: {entry['project_path']}\n"
        f"  Alternative: {entry['alternative']}\n"
        f"---\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)


def format_block_message(entry: dict) -> str:
    return (
        f"⚠️ COMMAND BLOCKED by pre-tool-use hook\n\n"
        f"**Command:** `{entry['command']}`\n\n"
        f"**Pattern matched:** {entry['pattern_name']}\n\n"
        f"**Reason:** {entry['reason']}\n\n"
        f"**Safe Alternative:** {entry['alternative']}\n\n"
        f"This has been logged to `{LOG_FILE}`.\n"
        f"Normal commands are not affected."
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: block-destructive-hook.py '<command>'")
        sys.exit(0)

    command = sys.argv[1]
    result = check_command(command)

    if result.get("blocked"):
        log_block(result)
        print(format_block_message(result))
        sys.exit(1)
    else:
        print(f"✅ Command allowed: `{command.strip()}`")
        sys.exit(0)


if __name__ == "__main__":
    main()
