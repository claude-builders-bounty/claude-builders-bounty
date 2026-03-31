#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before they are executed by Claude Code.
Logs every blocked attempt to ~/.claude/hooks/blocked.log.

Usage:
  - Place in ~/.claude/hooks/block-destructive.sh (symlink or copy)
  - Or run directly: python3 block-destructive.py
  - Reads JSON from stdin (Claude Code hook input format)
  - Exit 0 = allow, Exit 2 = block
"""

import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

# Dangerous command patterns
PATTERNS = [
    # rm -rf variants
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force)\b",
     "Recursive force delete (rm -rf)"),
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)\s+/",
     "Recursive delete from root/near-root path"),

    # SQL destructive commands
    (r"\bDROP\s+TABLE\b", "DROP TABLE statement"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE statement"),
    (r"\bTRUNCATE\b", "TRUNCATE statement"),
    (r"\bDELETE\s+FROM\b.*\b(WITHOUT|!)\s*WHERE\b", "DELETE without WHERE clause"),
    (r"\bDELETE\s+FROM\b(?!\s+\S+\s+WHERE)", "DELETE without WHERE clause"),

    # Git destructive commands
    (r"\bgit\s+push\s+.*--force\b", "Force push (git push --force)"),
    (r"\bgit\s+push\s+.*-f\b(?!-)", "Force push (git push -f)"),
    (r"\bgit\s+reset\s+--hard\b", "Hard reset (git reset --hard)"),
    (r"\bgit\s+clean\s+.*-fd\b", "Force clean (git clean -fd)"),
    (r"\bgit\s+branch\s+-D\b", "Force delete branch (git branch -D)"),

    # System destructive commands
    (r"\bmkfs\b", "Filesystem format (mkfs)"),
    (r"\bdd\s+.*of=/dev/", "Direct disk write (dd)"),
    (r":\(\)\{.*\|:&\};:", "Fork bomb"),
    (r"\bchmod\s+.*777\s+/", "Recursive chmod 777 on system path"),
    (r"\bchown\s+.*-R\s+/", "Recursive chown from root"),
    (r">\s*/dev/sd[a-z]", "Direct disk overwrite"),

    # Package manager destructive commands
    (r"\bpip\s+uninstall\s+.*-y", "Non-interactive pip uninstall"),
    (r"\bapt\s+(remove|purge)\s+.*-y", "Non-interactive apt remove"),
    (r"\brpm\s+.*--nodeps", "RPM with --nodeps"),
]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Log blocked command attempt to ~/.claude/hooks/blocked.log"""
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = f"[{timestamp}] BLOCKED | Reason: {reason} | Command: {command} | Project: {project_path}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any destructive pattern.
    Returns (is_blocked, reason).
    """
    for pattern, reason in PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.DOTALL):
            return True, reason
    return False, ""


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)

        data = json.loads(raw_input)
    except (json.JSONDecodeError, Exception):
        # If we can't parse, let it through (fail open)
        sys.exit(0)

    # Only intercept Bash tool calls
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    project_path = data.get("cwd", os.getcwd())

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_path)
        # Output message for Claude
        print(
            f"🚫 BLOCKED: This command was prevented by the safety hook.\n"
            f"   Reason: {reason}\n"
            f"   Command: {command}\n"
            f"\n"
            f"   If this action is genuinely needed, please ask the user to:\n"
            f"   1. Run the command manually in their terminal, OR\n"
            f"   2. Temporarily disable the hook by removing it from settings.json",
            file=sys.stderr
        )
        sys.exit(2)  # Exit code 2 = block in Claude Code hooks

    sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
