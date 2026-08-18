#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before execution and logs blocked attempts.
Designed for use with Claude Code's hooks system.

Blocked patterns:
  - rm -rf (recursive force delete)
  - git push --force / git push -f (force push)
  - DROP TABLE / DROP DATABASE (SQL destructive)
  - TRUNCATE (SQL truncate)
  - DELETE FROM without WHERE clause
  - dd if=/dev/zero (disk wipe)
  - mkfs (format filesystem)
  - chmod -R 777 (insecure permissions)
  - :(){ :|:& };: (fork bomb)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


BLOCKED_PATTERNS = [
    {
        "pattern": re.compile(r"\brm\s+.*-[^\s]*r[^\s]*f|rm\s+.*-[^\s]*f[^\s]*r|\brm\s+-rf\b|\brm\s+-fr\b"),
        "description": "rm -rf (recursive force delete)",
    },
    {
        "pattern": re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b"),
        "description": "git push --force (force push to remote)",
    },
    {
        "pattern": re.compile(r"\bDROP\s+(TABLE|DATABASE)\b", re.IGNORECASE),
        "description": "DROP TABLE/DATABASE (SQL destructive operation)",
    },
    {
        "pattern": re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "description": "TRUNCATE (SQL table truncation)",
    },
    {
        "pattern": re.compile(r"\bDELETE\s+FROM\s+\w+\s*;|\bDELETE\s+FROM\s+\w+\s*$", re.IGNORECASE),
        "description": "DELETE FROM without WHERE clause",
    },
    {
        "pattern": re.compile(r"\bdd\s+.*if=/dev/zero\b"),
        "description": "dd if=/dev/zero (disk wipe)",
    },
    {
        "pattern": re.compile(r"\bmkfs\b"),
        "description": "mkfs (format filesystem)",
    },
    {
        "pattern": re.compile(r"\bchmod\s+.*-R\s+777\b|\bchmod\s+777\s+-R\b"),
        "description": "chmod -R 777 (world-writable recursive permissions)",
    },
    {
        "pattern": re.compile(r":\(\)\s*\{\s*:\|:\&\s*\}\s*;?\s*:"),
        "description": "Fork bomb",
    },
]


def get_log_path():
    """Return the path to the blocked commands log file."""
    claude_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(claude_dir, exist_ok=True)
    return os.path.join(claude_dir, "blocked.log")


def log_blocked(command, reason, cwd):
    """Append a blocked command entry to the log file."""
    log_path = get_log_path()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | reason: {reason} | command: {command} | cwd: {cwd}\n"
    with open(log_path, "a") as f:
        f.write(entry)


def check_command(command):
    """Check if a command matches any blocked pattern. Returns (blocked, reason)."""
    for entry in BLOCKED_PATTERNS:
        if entry["pattern"].search(command):
            return True, entry["description"]
    return False, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    cwd = input_data.get("cwd", "unknown")
    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason, cwd)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"🚫 Blocked: {reason}. "
                    f"This command was intercepted by the destructive-command guard hook. "
                    f"If you need to run this command, disable the hook or modify your approach."
                ),
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
