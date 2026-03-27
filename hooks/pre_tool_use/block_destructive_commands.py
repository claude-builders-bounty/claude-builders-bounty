#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Place in ~/.claude/hooks/pre_tool_use/block_destructive_commands.py
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


BLOCKED_PATTERNS = [
    (r'rm\s+-[^\s]*r[^\s]*\s+-[^\s]*f[^\s]*|rm\s+-[^\s]*f[^\s]*\s+-[^\s]*r[^\s]*|rm\s+-rf|rm\s+-fr', "rm -rf (recursive force delete)"),
    (r'DROP\s+TABLE', "DROP TABLE (destructive SQL)"),
    (r'git\s+push\s+.*--force|git\s+push\s+.*-f(?:\s|$)', "git push --force (force push)"),
    (r'TRUNCATE(?:\s+TABLE)?\s+\w+', "TRUNCATE (destructive SQL)"),
    (r'DELETE\s+FROM\s+\w+(?:\s+WHERE\s+\S+)?', None),  # special handling below
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def is_delete_without_where(command: str) -> bool:
    """Returns True if command contains DELETE FROM without a WHERE clause."""
    pattern = re.compile(r'DELETE\s+FROM\s+\w+', re.IGNORECASE)
    if not pattern.search(command):
        return False
    where_pattern = re.compile(r'DELETE\s+FROM\s+\w+.*WHERE\s+\S+', re.IGNORECASE | re.DOTALL)
    return not where_pattern.search(command)


def check_command(command: str):
    """
    Check command against blocked patterns.
    Returns (blocked: bool, reason: str or None)
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if reason is None:
            # Special case: DELETE FROM without WHERE
            if is_delete_without_where(command):
                return True, "DELETE FROM without a WHERE clause (destructive SQL)"
        else:
            if re.search(pattern, command, re.IGNORECASE):
                return True, reason
    return False, None


def log_blocked(command: str, reason: str, project_path: str):
    """Append a blocked attempt to the log file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = (
        f"[{timestamp}] BLOCKED: {reason}\n"
        f"  Command: {command}\n"
        f"  Project: {project_path}\n"
        f"{'─' * 60}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        # If we can't parse input, allow the command through to avoid blocking normal use
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only intercept Bash tool calls
    if tool_name not in ("Bash", "bash", "shell"):
        # Not a bash tool — allow through
        print(json.dumps({"action": "allow"}))
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"action": "allow"}))
        sys.exit(0)

    # Determine project path from environment or cwd
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason, project_path)
        message = (
            f"🚫 Command blocked by safety hook.\n"
            f"Reason: {reason}\n"
            f"Command: {command}\n\n"
            f"This command was identified as potentially destructive and has been "
            f"prevented from executing. The attempt has been logged to:\n"
            f"  {LOG_PATH}\n\n"
            f"If you are certain this operation is safe and intended, please run it "
            f"manually in your terminal after reviewing its effects carefully."
        )
        response = {
            "action": "block",
            "message": message,
        }
        print(json.dumps(response))
        sys.exit(0)

    # Safe command — allow through
    print(json.dumps({"action": "allow"}))
    sys.exit(0)


if __name__ == "__main__":
    main()