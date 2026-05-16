#!/usr/bin/env python3
"""
block-destructive-bash.py — Claude Code PreToolUse hook
Blocks dangerous bash commands before execution.

Install: cp to ~/.claude/hooks/ and add to ~/.claude/settings.json
"""

import json
import sys
import os
import re
from datetime import datetime

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf variants
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\b", "rm -rf: recursive force delete"),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+/\b", "rm -r /: recursive delete from root"),
    # SQL destructive
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "DROP TABLE/DATABASE: irreversible data loss"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE: removes all rows without logging"),
    (r"\bDELETE\s+FROM\s+\w+\s*(?!.*\bWHERE\b)", "DELETE FROM without WHERE: deletes all rows"),
    # Git force push
    (r"\bgit\s+push\s+(-[a-zA-Z]*f|--force)\b", "git push --force: rewrites remote history"),
    (r"\bgit\s+push\s+.*--force-with-lease\b", None),  # Allow --force-with-lease (safe)
    # Disk/system destructive
    (r"\bmkfs\b", "mkfs: formats filesystem"),
    (r"\bdd\s+.*of=/dev/", "dd to device: overwrites disk"),
    (r">\s*/dev/sd[a-z]", "redirect to block device: overwrites disk"),
    # chmod/chown dangerous
    (r"\bchmod\s+(-R|--recursive)\s+777\s+/", "chmod -R 777 /: removes all file permissions"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def check_command(command: str) -> list[str]:
    """Check a command against dangerous patterns. Returns list of reasons if blocked."""
    reasons = []
    for pattern, reason in DANGEROUS_PATTERNS:
        if reason is None:
            continue  # Skip allowlisted patterns
        if re.search(pattern, command, re.IGNORECASE):
            reasons.append(reason)
    return reasons


def log_blocked(command: str, reasons: list[str], project_path: str):
    """Log blocked command to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reasons": reasons,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    """Main hook entry point. Reads JSON from stdin, checks for dangerous commands."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, allow the command (don't break normal flow)
        sys.exit(0)

    # PreToolUse hook receives tool_name and tool_input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check for dangerous patterns
    reasons = check_command(command)

    if reasons:
        project_path = input_data.get("project_path", os.getcwd())
        log_blocked(command, reasons, project_path)

        # Print explanation to stderr (Claude sees this)
        print(
            f"🚫 BLOCKED: This command was blocked by the safety hook.\n"
            f"Command: {command}\n"
            f"Reasons:\n" + "\n".join(f"  - {r}" for r in reasons) + "\n\n"
            f"If you need to run this command, ask the user for explicit confirmation.",
            file=sys.stderr,
        )
        # Exit code 2 = block the tool call
        sys.exit(2)

    # Exit code 0 = allow
    sys.exit(0)


if __name__ == "__main__":
    main()
