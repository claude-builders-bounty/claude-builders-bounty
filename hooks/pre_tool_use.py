#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: blocks destructive bash commands.

Reads a JSON payload from stdin (Claude Code hook format), checks the command
against dangerous patterns, and returns a block/allow decision.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that should be BLOCKED
DESTRUCTIVE_PATTERNS = [
    {
        "regex": r"\brm\s+.*-[a-zA-Z]*[rR].*-[a-zA-Z]*[fF]|\brm\s+.*-[a-zA-Z]*[fF].*-[a-zA-Z]*[rR]|\brm\s+-rf\b|\brm\s+-fr\b",
        "reason": "rm -rf (recursive force delete) — could cause irreversible data loss",
        "category": "filesystem",
    },
    {
        "regex": r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|FUNCTION|PROCEDURE)\b",
        "reason": "SQL DROP statement — irreversible schema destruction",
        "category": "database",
    },
    {
        "regex": r"\bgit\s+push\s+.*(--force|--force-with-lease|-f)\b",
        "reason": "git push --force — overwrites remote history",
        "category": "git",
    },
    {
        "regex": r"\bTRUNCATE\s+(TABLE\s+)?",
        "reason": "TRUNCATE statement — wipes all rows from a table",
        "category": "database",
    },
    {
        "regex": r"\bDELETE\s+FROM\s+\S+\s*(;|\s*$)",
        "reason": "DELETE FROM without WHERE clause — deletes all rows",
        "category": "database",
    },
    {
        "regex": r"\bgit\s+reset\s+--hard\b",
        "reason": "git reset --hard — discards all uncommitted changes",
        "category": "git",
    },
    {
        "regex": r"\bchmod\s+-?\s*777\b",
        "reason": "chmod 777 — makes files world-writable, security risk",
        "category": "filesystem",
    },
    {
        "regex": r"\bmkfs[.\w]*\b",
        "reason": "mkfs — formats a filesystem, irreversible data loss",
        "category": "system",
    },
    {
        "regex": r"\bdd\s+.*of=/dev/\S+",
        "reason": "dd to device — can wipe entire disk",
        "category": "system",
    },
    {
        "regex": r"\b(curl|wget)\b.*\|\s*(bash|sh|zsh|python|perl|ruby)\b",
        "reason": "Piping remote script to shell — untrusted code execution",
        "category": "network",
    },
]

# DELETE FROM ... WHERE is SAFE — handled after the catch-all above
SAFE_DELETE_REGEX = re.compile(r"\bDELETE\s+FROM\s+\S+\s+WHERE\b", re.IGNORECASE)


def log_blocked(command: str, reason: str, category: str) -> None:
    """Append a blocked attempt to the log file."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        project = os.getcwd()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{timestamp}] BLOCKED [{category.upper()}]: {reason}\n"
                f"  command: {command}\n"
                f"  project: {project}\n\n"
            )
    except Exception:
        pass  # Logging should never prevent execution


def check_command(command: str) -> dict | None:
    """
    Check a command against destructive patterns.
    Returns a block decision dict, or None if safe.
    """
    # Safe DELETE FROM ... WHERE should pass even though DELETE FROM matches
    if SAFE_DELETE_REGEX.search(command):
        return None

    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern["regex"], command, re.IGNORECASE):
            return {
                "decision": "block",
                "reason": pattern["reason"],
                "category": pattern["category"],
            }
    return None


def main():
    """Main entry point. Reads JSON from stdin, writes decision to stdout."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input → pass through
            sys.exit(0)

        payload = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Fail open — if we can't parse, let the command through
        sys.exit(0)

    # Only intercept Bash / ExecuteCommand tool calls
    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Bash", "ExecuteCommand", "Write", "Edit"):
        sys.exit(0)

    # Extract the command string
    tool_input = payload.get("tool_input", {})
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "") or tool_input.get("input", "")
    if isinstance(tool_input, str):
        command = tool_input

    if not command:
        sys.exit(0)

    result = check_command(command)
    if result:
        log_blocked(command, result["reason"], result["category"])

        # Claude Code hook response format
        response = {
            "decision": "block",
            "reason": result["reason"],
            "category": result["category"],
        }
        print(json.dumps(response, indent=2))
        sys.exit(2)

    # Safe command — pass through silently
    sys.exit(0)


if __name__ == "__main__":
    main()
