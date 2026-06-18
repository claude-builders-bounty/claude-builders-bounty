#!/usr/bin/env python3
"""
pre-tool-use-block-destructive.py
Claude Code pre-tool-use hook that blocks destructive bash commands.

Blocks: rm -rf, DROP TABLE/DATABASE, TRUNCATE, DELETE FROM without WHERE,
git push --force/-f.

Installation (2 steps):
    1. mkdir -p ~/.claude/hooks
    2. Add to ~/.claude/settings.json:
       {
         "hooks": {
           "PreToolUse": [{
             "matcher": "Bash",
             "hooks": [{"type": "command",
                        "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"}]
           }]
         }
       }
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Each entry: (regex, reason). Order matters (most specific first).
BLOCKED_PATTERNS: list[tuple[str, str]] = [
    # rm with -r and -f in any order
    (r"\brm\s+(?:-(?:[\-rRfF]+|-[rR][fF]|-[fF][rR]|\s+-\S+){1,5})\s+/\S*",
     "recursive force delete (rm -rf) on absolute path"),
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF]\b", "rm with -r and -f flags"),
    (r"\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*[rR]\b", "rm with -f and -r flags"),

    # SQL destructive
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|FUNCTION|PROCEDURE)\b",
     "SQL DROP statement"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "SQL TRUNCATE statement"),
    # DELETE FROM without WHERE (multiline)
    (r"\bDELETE\s+FROM\s+\w+(?:\s+(?!WHERE\b)\w+)*\s*;",
     "SQL DELETE FROM without WHERE clause"),
    (r"\bDELETE\s+FROM\s+\w+\s*$", "SQL DELETE FROM without WHERE clause"),

    # git push force
    (r"\bgit\s+push\s+(?:-[a-zA-Z]*f|--force(?:-with-lease)?)\b",
     "git push --force (use --force-with-lease if needed)"),
]


def check_command(command: str) -> tuple[bool, str | None]:
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
            return True, reason
    return False, None


def log_blocked(command: str, reason: str, project: str = "") -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] BLOCKED: {reason}\n")
        f.write(f"  command: {command.strip()}\n")
        if project:
            f.write(f"  project: {project}\n")
        f.write("\n")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return 0  # Not a hook call, allow

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return 0  # Only block Bash commands

    tool_input = data.get("tool_input", {}) or {}
    command = tool_input.get("command", "")
    project = data.get("cwd", "")

    if not command:
        return 0

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, reason, project)
        decision = {
            "decision": "block",
            "reason": (
                f"Blocked by pre-tool-use-block-destructive: {reason}.\n"
                f"Command: {command}\n"
                f"If this is intentional, ask the user to confirm before proceeding."
            ),
        }
        print(json.dumps(decision))
        return 0

    return 0  # Allow normal commands


if __name__ == "__main__":
    sys.exit(main())
