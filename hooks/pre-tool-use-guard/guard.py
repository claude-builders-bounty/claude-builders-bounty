#!/usr/bin/env python3
"""
Claude Code Pre-tool-use Hook: Destructive Command Guard
=========================================================

A pre-tool-use hook that intercepts and blocks dangerous bash commands
before Claude Code executes them. Protects against accidental data loss,
database destruction, and force-pushes.

Blocked patterns:
  - rm -rf           (recursive force delete)
  - DROP TABLE       (SQL table deletion)
  - git push --force (force push to remote)
  - TRUNCATE         (SQL table truncation)
  - DELETE FROM      (SQL delete without WHERE clause)

Usage:
  This script reads JSON from stdin (Claude Code hook protocol),
  inspects the command, and returns a deny decision if a destructive
  pattern is detected. Safe commands pass through unmodified.

See: https://docs.anthropic.com/en/docs/claude-code/hooks
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Each rule: (compiled regex, human-readable description)
DESTRUCTIVE_PATTERNS = [
    (
        re.compile(r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b|\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b", re.IGNORECASE),
        "rm -rf (recursive force delete)",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE (SQL table deletion)",
    ),
    (
        re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b", re.IGNORECASE),
        "git push --force (force push to remote)",
    ),
    (
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE (SQL table truncation)",
    ),
]

# Special pattern: DELETE FROM without WHERE
DELETE_WITHOUT_WHERE = re.compile(
    r"\bDELETE\s+FROM\s+\S+\s*;?\s*$", re.IGNORECASE | re.MULTILINE
)


# ── Core Logic ─────────────────────────────────────────────────────────


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any destructive pattern.

    Returns:
        (is_blocked, reason) — True + reason if blocked, False + "" if safe.
    """
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, description

    # DELETE FROM without WHERE clause
    if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        # Allow if WHERE is present after DELETE FROM <table>
        if not re.search(r"\bDELETE\s+FROM\s+\S+\s+WHERE\b", command, re.IGNORECASE):
            return True, "DELETE FROM without WHERE clause (unsafe mass delete)"

    return False, ""


def log_blocked(command: str, reason: str, project_dir: str) -> None:
    """Append a blocked-command entry to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Pattern : {reason}\n"
        f"  Command : {command}\n"
        f"  Project : {project_dir}\n"
        f"{'─' * 60}\n"
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def deny(reason: str, command: str) -> None:
    """Output a deny decision in Claude Code hook JSON format and exit."""
    message = (
        f"🚫 BLOCKED by pre-tool-use guard\n"
        f"   Reason: {reason}\n"
        f"   Command: {command}\n"
        f"   This command was blocked to prevent accidental data loss.\n"
        f"   If you need to run this command, ask the user for explicit confirmation."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    json.dump(output, sys.stdout)
    sys.exit(0)


def main() -> None:
    """Entry point: read hook input from stdin, check, decide."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Can't parse input → don't block, let it pass
        sys.exit(0)

    # Extract the command from tool_input
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        # No command to inspect → allow
        sys.exit(0)

    # Get project directory from the hook input
    project_dir = hook_input.get("cwd", os.getcwd())

    # Check against destructive patterns
    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_dir)
        deny(reason, command)
    else:
        # Safe command → exit 0 (allow)
        sys.exit(0)


if __name__ == "__main__":
    main()
