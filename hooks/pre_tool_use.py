#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks dangerous bash commands.

This hook intercepts bash commands and prevents execution of dangerous patterns
such as recursive force deletion, SQL destruction, and force pushes.

All blocked attempts are logged to ~/.claude/hooks/blocked.log with:
- Timestamp (ISO 8601)
- Attempted command
- Project path
- Reason for block
"""

import json
import sys
import os
import re
from datetime import datetime, timezone


def main():
    """Main hook entry point - reads JSON from stdin, outputs JSON decision."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return_result({"permissionDecision": "allow"})
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    project_path = input_data.get("project_path", "")

    # Only check bash commands
    if tool_name != "bash" or not command:
        return_result({"permissionDecision": "allow"})
        return

    # Check against dangerous patterns
    blocked_pattern = check_dangerous_patterns(command)

    if blocked_pattern:
        log_blocked_command(command, project_path, blocked_pattern)
        return_result({
            "permissionDecision": "deny",
            "reason": f"Blocked dangerous command: {blocked_pattern}"
        })
        return

    # Safe command - allow it
    return_result({"permissionDecision": "allow"})


def check_dangerous_patterns(command):
    """
    Check if command matches any dangerous patterns.

    Returns:
        str: Pattern name if dangerous, None if safe
    """
    patterns = {
        "rm_recursive_force": [
            r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*)",
            r"\brm\s+-+f\s+-+r",
            r"\brm\s+-+r\s+-+f",
        ],
        "drop_table": [
            r"\bDROP\s+TABLE\b",
            r"\bDROP\s+DATABASE\b",
        ],
        "truncate": [
            r"\bTRUNCATE\b",
        ],
        "delete_without_where": [
            r"\bDELETE\s+FROM\s+(?!\w+.*\bWHERE\b)",
        ],
        "git_force_push": [
            r"\bgit\s+push\s+.*(-f\b|--force\b|--force-with-lease\b)",
            r"\bgit\s+push\s+(-f|--force|--force-with-lease)",
        ],
    }

    for pattern_name, regex_patterns in patterns.items():
        for regex_pattern in regex_patterns:
            if re.search(regex_pattern, command, re.IGNORECASE):
                return pattern_name

    return None


def log_blocked_command(command, project_path, reason):
    """Log blocked command to ~/.claude/hooks/blocked.log as JSON."""
    try:
        log_dir = os.path.expanduser("~/.claude/hooks")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "blocked.log")

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "command": command,
            "project": project_path,
            "reason": f"Dangerous pattern: {reason}"
        }

        with open(log_file, "a") as f:
            json.dump(entry, f)
            f.write("\n")
    except Exception:
        # Silently fail on logging errors - don't block the hook
        pass


def return_result(result):
    """Output JSON result to stdout."""
    json.dump(result, sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()