#!/usr/bin/env python3
"""
Bash Guard -- Claude Code pre-tool-use hook.

Intercepts dangerous bash commands before they execute.
Blocks destructive patterns and logs attempts.

Install: cp bash_guard.py ~/.claude/hooks/
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# Path to log file
LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that trigger a block
BLOCK_PATTERNS = [
    # rm -rf (with or without path)
    re.compile(r"rm\s+-rf", re.IGNORECASE),
    # rm -r -f variations
    re.compile(r"rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+.*-[a-zA-Z]*r|.*-r.*\s+-.*f)", re.IGNORECASE),
    # DROP TABLE
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    # TRUNCATE TABLE
    re.compile(r"TRUNCATE\s+TABLE", re.IGNORECASE),
    # git push --force
    re.compile(r"git\s+push\s+.*--force", re.IGNORECASE),
    # git push -f
    re.compile(r"git\s+push\s+.*\s+-f\b", re.IGNORECASE),
    # DELETE FROM without WHERE
    re.compile(r"DELETE\s+FROM\s+(?!.*\bWHERE\b).+$", re.IGNORECASE),
    # Shred (secure deletion)
    re.compile(r"\bshred\b", re.IGNORECASE),
    # mkfs / format
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    # dd to disk (not iso files)
    re.compile(r"\bdd\b.*of=/dev/[sh]d[a-z]", re.IGNORECASE),
    # :(){:|:&};: fork bomb
    re.compile(r":\(\)\s*\{\s*:\|:&\s*\};\s*:", re.IGNORECASE),
]

# Patterns that are safe (allowed even if they contain block-like substrings)
SAFE_PATTERNS = [
    # rm -rf in test directories
    re.compile(r"rm\s+-rf\s+.*(test|temp|tmp|build|dist|\.pytest|__pycache__|node_modules|\.venv|target|\.git)", re.IGNORECASE),
]


def log_blocked(command, reason, project_path=""):
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


def is_dangerous(command):
    """Check if a command matches any dangerous pattern."""
    # First check if explicitly safe
    for safe in SAFE_PATTERNS:
        if safe.search(command):
            return False, ""

    for pattern in BLOCK_PATTERNS:
        match = pattern.search(command)
        if match:
            return True, f"Matched pattern: {pattern.pattern[:60]}..."
    return False, ""


def main():
    """Read tool-use request from stdin, validate bash commands."""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not a valid JSON request -- pass through unchanged
        print(json.dumps({"approved": True}))
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only intercept bash tool
    if tool_name != "bash":
        print(json.dumps({"approved": True}))
        return

    command = tool_input.get("command", "")
    project_path = tool_input.get("project_path", os.getcwd())

    dangerous, reason = is_dangerous(command)

    if dangerous:
        log_blocked(command, reason, project_path)
        response = {
            "approved": False,
            "message": (
                f"[BASH GUARD] This command was blocked: {command}\n"
                f"Reason: {reason}\n"
                "\n"
                "This command matches a known destructive pattern. "
                "If you believe this is a false positive, you can:\n"
                "  1. Run the command manually outside Claude Code, OR\n"
                "  2. Edit ~/.claude/hooks/bash_guard.py to adjust the pattern\n"
                f"\nLogged to: {LOG_PATH}"
            ),
        }
        print(json.dumps(response))
        return

    # Safe command -- approve
    print(json.dumps({"approved": True}))


if __name__ == "__main__":
    main()
