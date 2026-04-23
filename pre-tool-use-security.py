#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook

Intercepts and blocks dangerous bash commands before execution.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE without WHERE

Logs all blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    # File system destruction
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\b',
     "rm -rf (recursive force delete)"),

    # Git force operations
    (r'\bgit\s+push\s+(-[a-zA-Z]*f|--force|--force-with-lease)\b',
     "git push --force (overwrites remote history)"),

    # SQL destruction without safety
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b',
     "DROP TABLE/DATABASE/SCHEMA (permanent deletion)"),

    (r'\bTRUNCATE\s+TABLE\b',
     "TRUNCATE TABLE (deletes all rows)"),

    (r'\bDELETE\s+FROM\s+(?!.*\bWHERE\b)',
     "DELETE FROM without WHERE clause (deletes all rows)"),
]


def check_command(command: str) -> tuple[bool, str | None]:
    """
    Check if command contains dangerous patterns.

    Returns:
        (is_safe, reason_if_blocked)
    """
    command_normalized = " ".join(command.split())

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command_normalized, re.IGNORECASE):
            return False, reason

    return True, None


def log_blocked_attempt(command: str, reason: str, project_path: str):
    """Log blocked command attempt to ~/.claude/hooks/blocked.log"""
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n"
    log_entry += f"  Command: {command}\n"
    log_entry += f"  Project: {project_path}\n\n"

    with open(log_file, "a") as f:
        f.write(log_entry)


def main():
    """Main hook entry point - receives JSON from Claude Code"""
    try:
        # Read input from stdin (Claude Code passes JSON)
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool", {}).get("name", "")

        # Only intercept Bash tool calls
        if tool_name != "Bash":
            # Allow all other tools
            print(json.dumps({"allowed": True}))
            return

        # Extract command from Bash tool parameters
        command = input_data.get("tool", {}).get("input", {}).get("command", "")
        project_path = input_data.get("cwd", "unknown")

        # Check if command is safe
        is_safe, reason = check_command(command)

        if is_safe:
            # Allow safe commands
            print(json.dumps({"allowed": True}))
        else:
            # Block dangerous commands
            log_blocked_attempt(command, reason or "Unknown dangerous pattern", project_path)

            # Return denial with explanation
            response = {
                "allowed": False,
                "message": f"⚠️  BLOCKED: {reason}\n\n"
                          f"Command: {command}\n\n"
                          f"This command has been blocked for safety. "
                          f"If you need to run it, use the ! prefix to bypass this hook.\n\n"
                          f"Logged to: ~/.claude/hooks/blocked.log"
            }
            print(json.dumps(response))

    except Exception as e:
        # On error, allow command (fail-open to avoid breaking Claude)
        print(json.dumps({
            "allowed": True,
            "message": f"Security hook error (allowing command): {str(e)}"
        }), file=sys.stderr)


if __name__ == "__main__":
    main()
