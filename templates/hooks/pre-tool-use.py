#!/usr/bin/env python3
"""
pre-tool-use.py — Claude Code Pre-Tool-Use Security Hook

Blocks dangerous bash commands before execution.
Installs to ~/.claude/hooks/pre-tool-use

Blocked patterns:
  - rm -rf (recursive forced deletion)
  - DROP TABLE (database destruction)
  - git push --force / --force-with-lease (history rewriting)
  - TRUNCATE (bulk data deletion)
  - DELETE FROM without WHERE clause (unfiltered deletion)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# === Configuration ===
HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOK_DIR / "blocked.log"

DANGEROUS_PATTERNS = [
    # Recursive deletion
    ("rm -rf", "Recursive forced deletion is irreversible. Use 'trash' or 'rm' with explicit file paths."),
    ("rm -fr", "Recursive forced deletion is irreversible. Use 'trash' or 'rm' with explicit file paths."),
    ("rm --recursive --force", "Recursive forced deletion is irreversible."),
    # Database destruction
    ("DROP TABLE", "Dropping database tables is destructive. Use migrations or backup first."),
    ("DROP DATABASE", "Dropping databases is destructive and irreversible."),
    ("DROP SCHEMA", "Dropping schemas is destructive and irreversible."),
    ("TRUNCATE", "TRUNCATE permanently removes all rows. Use DELETE with a WHERE clause, or backup first."),
    # Unfiltered deletion
    ("DELETE FROM", None),  # Special case: check for WHERE clause
    # Git history rewriting
    ("git push --force", "Force-pushing rewrites shared history. Use 'git push --force-with-lease' with caution and team coordination."),
    ("git push -f", "Force-pushing rewrites shared history. Use with caution."),
]


def log_blocked(cmd: str, reason: str, project_path: str):
    """Log a blocked command attempt."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] BLOCKED | project={project_path} | reason={reason} | cmd={cmd}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Check a command against dangerous patterns.
    Returns (is_blocked, reason_message).
    """
    command_lower = command.lower().strip()

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.lower() in command_lower:
            if pattern == "DELETE FROM" and "where" in command_lower:
                continue  # WHERE clause present — allow
            if pattern == "DELETE FROM" and "where" not in command_lower:
                return (True, "DELETE FROM without WHERE clause deletes all rows. Add a WHERE clause or use LIMIT.")
            return (True, reason)

    return (False, "")


def main():
    """Main hook entry point."""
    # Read the tool use request from stdin
    try:
        raw = sys.stdin.read()
        if not raw:
            return
        request = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return  # Malformed input — let Claude proceed

    # Extract the command from tool_use
    tool_use = request.get("tool_use", {})
    tool_name = tool_use.get("tool_name", "")

    # We only intercept Bash tool calls
    if tool_name != "Bash":
        return

    # Get the command argument
    cmd = tool_use.get("input", {}).get("command", "")
    if not cmd:
        return

    # Get the project context
    project_path = os.getcwd()

    # Check for dangerous patterns
    blocked, reason = check_command(cmd)
    if blocked:
        log_blocked(cmd, reason, project_path)
        result = {
            "tool_result": (
                f"⛔ **Command Blocked by Security Hook**\n\n"
                f"**Reason:** {reason}\n\n"
                f"**Attempted:** `{cmd}`\n\n"
                f"---\n"
                f"📝 This command has been logged to `~/.claude/hooks/blocked.log`\n"
                f"💡 If you need to run this command intentionally, temporarily disable the hook:\n"
                f"   `mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled`\n"
                f"   Then re-enable it after: `mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use`"
            ),
            "is_error": False,
            "status": "blocked_by_security_hook",
        }
        print(json.dumps(result))
        sys.exit(0)


if __name__ == "__main__":
    main()
