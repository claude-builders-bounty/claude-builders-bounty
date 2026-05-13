#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands.

Receives JSON on stdin with the intended tool call.
Returns JSON on stdout with the (possibly modified) tool call.
See: https://docs.anthropic.com/claude-code/hooks
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
LOG_DIR = os.path.dirname(LOG_FILE)

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    re.compile(r'\brm\s+-rf\b', re.IGNORECASE),
    re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
    re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
    re.compile(r'\bgit\s+push\s+--force\b', re.IGNORECASE),
    re.compile(r'\bgit\s+push\s+-f\b', re.IGNORECASE),
]

# Patterns that require extra caution (DELETE FROM without WHERE)
CONDITIONAL_PATTERNS = [
    re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE),
]


def has_where(command: str) -> bool:
    """Check if a DELETE FROM statement has a WHERE clause."""
    lines = command.split("\n")
    for line in lines:
        if re.search(r'\bDELETE\s+FROM\b', line, re.IGNORECASE):
            if not re.search(r'\bWHERE\b', command, re.IGNORECASE):
                return False
    return True


def should_block(command: str) -> tuple:
    """
    Check if a command should be blocked.
    Returns (should_block: bool, reason: str).
    """
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return (True, f"Command blocked: contains unsafe pattern `{pattern.pattern}`")

    if CONDITIONAL_PATTERNS[0].search(command) and not has_where(command):
        return (True, "Command blocked: `DELETE FROM` without a `WHERE` clause")

    return (False, "")


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Log a blocked attempt to the log file."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "command": command,
            "reason": reason,
            "project_path": project_path,
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silently fail if we can't log


def safe_command(command: str) -> str:
    """Try to offer a safer alternative."""
    # Replace rm -rf with safer alternatives
    if re.search(r'\brm\s+-rf\b', command, re.IGNORECASE):
        # Suggest using trash or a more targeted rm
        return command.replace("-rf", "-ri")

    return command


def get_project_path() -> str:
    """Try to get the current project path from cwd or env."""
    try:
        return os.getcwd()
    except Exception:
        return os.environ.get("PROJECT_PATH", "unknown")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # Nothing to process, pass through
            print(json.dumps({"tool": None}))
            return

        data = json.loads(raw)

        # Only process Bash tool calls
        tool = data.get("tool", {})
        if tool.get("name") != "Bash":
            # Pass through non-bash calls unchanged
            print(json.dumps(data))
            return

        command = tool.get("input", {}).get("command", "")
        if not command:
            print(json.dumps(data))
            return

        should_block_result, reason = should_block(command)

        if should_block_result:
            project_path = get_project_path()
            log_blocked(command, reason, project_path)

            # Return an error to block the command
            error_msg = (
                f"⛔ {reason}\n\n"
                f"To proceed, use a more targeted command or explicitly "
                f"confirm with the user."
            )

            # Some commands have safe alternatives
            alt = safe_command(command)
            if alt != command:
                error_msg += f"\n\n💡 Safer alternative: `{alt}`"

            result = {
                "tool": None,
                "error": error_msg,
            }
            print(json.dumps(result))
            return

        # Pass through allowed commands
        print(json.dumps(data))

    except json.JSONDecodeError:
        # If we can't parse the input, pass through
        print(raw)
    except Exception:
        # On any error, allow the command through (fail-open)
        if "raw" in dir():
            print(raw)
        else:
            print(json.dumps({"tool": None}))


if __name__ == "__main__":
    main()
