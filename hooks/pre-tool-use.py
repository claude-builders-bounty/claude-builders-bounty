#!/usr/bin/env python3
"""
Pre-tool-use hook: Blocks destructive bash commands in Claude Code.
Part of claude-builders-bounty — $100 Bounty
"""

import os
import sys
import json
import re
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")

# Patterns that are always blocked (case-insensitive)
BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b',         "Unconditional recursive delete"),
    (r'\brm\s+--recursive\b', "Recursive delete"),
    (r'\bDROP\s+TABLE\b',     "Destructive database operation"),
    (r'\bgit\s+push\s+--force\b', "Force-push to git (overwrites history)"),
    (r'\bTRUNCATE\b',         "Destructive database operation"),
    (r'\bDELETE\s+FROM\b(?!\s*.*\bWHERE\b)', "DELETE without WHERE clause"),
]

# Commands that are okay to bypass (for legitimate use cases)
SAFE_BYPASS_PATTERNS = [
    r'\brm\s+-rf\s+/tmp/',   # Clearing temp directories
    r'\brm\s+-rf\s+node_modules',  # Cleaning node_modules
    r'\brm\s+-rf\s+\.git/',  # Git operations (rare but sometimes needed)
]


def read_stdin():
    """Read JSON input from Claude Code."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def write_stdout(data):
    """Write JSON output to stdout for Claude Code."""
    sys.stdout.write(json.dumps(data))
    sys.stdout.flush()


def log_blocked(command, reason, cwd):
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Reason:  {reason}\n"
        f"  Command: {command}\n"
        f"  Project: {cwd}\n"
        f"  {'─' * 50}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_safe_bypass(command):
    """Check if a blocked-looking command is actually safe."""
    for pattern in SAFE_BYPASS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def check_command(command):
    """Check a command against blocked patterns. Returns (blocked, reason)."""
    if not command or not isinstance(command, str):
        return False, ""

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check if it's a known safe use
            if check_safe_bypass(command):
                return False, ""
            return True, reason

    return False, ""


def main():
    input_data = read_stdin()
    
    if not input_data:
        # No data — nothing to check
        write_stdout({"result": "allowed"})
        return

    # Claude Code pre-tool-use hook receives tool use data
    # We look for bash commands in the data
    tool_name = input_data.get("toolName") or input_data.get("name", "")
    tool_input = input_data.get("toolInput") or input_data.get("input", {})
    cwd = input_data.get("cwd") or input_data.get("path", os.getcwd())

    # Only intercept bash/exec tools
    if tool_name not in ("Bash", "bash", "execute_command", "exec", "run"):
        write_stdout({"result": "allowed"})
        return

    # Extract the command
    command = ""
    if isinstance(tool_input, dict):
        command = (
            tool_input.get("command", "")
            or tool_input.get("cmd", "")
            or json.dumps(tool_input)
        )
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        write_stdout({"result": "allowed"})
        return

    # Check if command is dangerous
    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason, cwd)
        write_stdout({
            "result": "blocked",
            "error": (
                f"⚠️  **Command Blocked for Safety**\n\n"
                f"This command was blocked because it contains: **{reason}**\n\n"
                f"```\n{command}\n```\n\n"
                f"Blocked attempt logged to: `{LOG_FILE}`\n\n"
                f"💡 Tip: If you need to run this command, use a more specific path "
                f"(e.g., `rm -rf ./specific-dir/`) or manually review before executing."
            )
        })
    else:
        write_stdout({"result": "allowed"})


if __name__ == "__main__":
    main()
