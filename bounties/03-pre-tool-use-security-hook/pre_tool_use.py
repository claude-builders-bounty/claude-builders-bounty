#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Destructive Bash Commands

Intercepts bash commands and blocks dangerous patterns before execution.
Logs all blocked attempts to ~/.claude/hooks/blocked.log.

Installation:
    1. Copy this file to ~/.claude/hooks/pre_tool_use.py
    2. Add to ~/.claude/settings.json:
       {
         "hooks": {
           "PreToolUse": [
             {
               "matcher": "Bash",
               "hooks": [
                 {
                   "type": "command",
                   "command": "python3 ~/.claude/hooks/pre_tool_use.py"
                 }
               ]
             }
           ]
         }
       }

Reference: https://docs.anthropic.com/claude-code/hooks
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Configuration
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
PROJECT_PATH = os.getcwd()

# Dangerous patterns (regex)
DANGEROUS_PATTERNS = [
    # rm -rf / rm -fr / rm -Rf etc (with various flags)
    (r"\brm\s+(-[rRfF]*[rRfF][rRfF]*|-[rR][fF]|-[fF][rR])\b", "rm -rf: recursive force delete"),
    # DROP TABLE / DROP DATABASE
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b", "DROP statement: destructive DDL"),
    # git push --force / git push -f (with or without upstream)
    (r"\bgit\s+push\s+(--force(|-with-lease)?|-f\b)", "git push --force: force push"),
    # TRUNCATE TABLE
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE: deletes all rows"),
    # DELETE FROM without WHERE clause (negative lookahead for WHERE)
    # Allow: DELETE FROM x WHERE y
    # Block: DELETE FROM x; or DELETE FROM x
    (r"\bDELETE\s+FROM\s+\w+", "DELETE FROM without WHERE: deletes all rows"),
]

# Patterns that allow a DELETE FROM to pass (legitimate use with WHERE)
DELETE_WHITELIST = r"\bDELETE\s+FROM\s+\w+.*\bWHERE\b"

# Whitelist (legitimate patterns that might look dangerous)
WHITELIST_PATTERNS = [
    # rm with specific file paths and no recursive flag
    r"\brm\s+[^-\s]\S*\s*$",
    # git push without --force or -f
    r"\bgit\s+push\b(?!.*--force)(?!.*-f\b)",
    # SELECT statements
    r"\bSELECT\b",
]


def log_blocked(command: str, reason: str) -> None:
    """Append blocked attempt to log file."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] BLOCKED\n")
            f.write(f"  Project: {PROJECT_PATH}\n")
            f.write(f"  Reason:  {reason}\n")
            f.write(f"  Command: {command}\n")
            f.write("-" * 80 + "\n")
    except OSError as e:
        # Don't fail the hook if logging fails
        print(f"[hook] Warning: failed to write log: {e}", file=sys.stderr)


def is_whitelisted(command: str) -> bool:
    """Check if command matches a legitimate (non-destructive) pattern."""
    for pattern in WHITELIST_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command is dangerous.
    Returns: (is_dangerous, reason)
    """
    # First check whitelist
    if is_whitelisted(command):
        return False, ""

    # Special handling for DELETE FROM: allow if it has WHERE clause
    if re.match(r"^\s*DELETE\s+FROM\s", command, re.IGNORECASE):
        if re.search(DELETE_WHITELIST, command, re.IGNORECASE | re.DOTALL):
            return False, ""  # Has WHERE - allowed

    # Then check dangerous patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
            return True, reason

    return False, ""


def main() -> int:
    """
    Main hook entry point.
    Reads JSON from stdin (Claude Code hook format).
    Exits 0 to allow, exits 2 to block (with stderr message).
    """
    try:
        # Read hook input from stdin
        hook_input = sys.stdin.read()
        if not hook_input.strip():
            return 0

        data = json.loads(hook_input)

        # Extract the tool name and command
        tool_name = data.get("tool_name", "")
        if tool_name != "Bash":
            return 0  # Only intercept Bash tool

        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            return 0

        # Check if command is dangerous
        is_dangerous, reason = check_command(command)

        if is_dangerous:
            # Log the blocked attempt
            log_blocked(command, reason)

            # Display clear message to Claude (printed to stderr)
            # Exit code 2 blocks the tool call and shows stderr to Claude
            print(
                f"🚫 BLOCKED by pre-tool-use security hook\n"
                f"Reason: {reason}\n"
                f"Command: {command}\n"
                f"\n"
                f"This hook prevents destructive operations. If you genuinely need "
                f"to run this command, ask the user to run it manually outside of Claude Code.\n"
                f"\n"
                f"Pattern blocked: {reason}\n"
                f"Log: {LOG_PATH}",
                file=sys.stderr,
            )
            return 2  # Exit 2 = block tool call in Claude Code

        return 0  # Allow the command

    except json.JSONDecodeError:
        # Invalid JSON input - allow (don't block on parse errors)
        return 0
    except Exception as e:
        # Unexpected error - log but don't block
        print(f"[hook] Error: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
