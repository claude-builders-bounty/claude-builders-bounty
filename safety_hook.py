#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
Blocks destructive bash commands before execution.

Install:
  cp safety_hook.py ~/.claude/hooks/safety_hook.py
  echo '{"hooks":{"PreToolUse":[{"command":"python3 ~/.claude/hooks/safety_hook.py","matcher":"Bash","type":"command"}]}}' > ~/.claude/settings.json
"""

import sys
import json
import os
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+-[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*r[a-zA-Z]*\s+-[a-zA-Z]*f[a-zA-Z]*|-rf\b|-fr\b|--recursive\b.*--force\b)', 'recursive force delete'),
    (r'\bDROP\s+TABLE\b', 'SQL DROP TABLE'),
    (r'\bgit\s+push\s+.*--force\b', 'force push to git'),
    (r'\bTRUNCATE\s+', 'SQL TRUNCATE'),
    (r'\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)', 'SQL DELETE without WHERE clause'),
]

ALLOWED_PATTERNS = [
    r'\brm\s+-rf\s+/tmp/',
    r'\brm\s+-rf\s+.*test',
    r'\brm\s+-rf\s+node_modules',
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def load_allow_config():
    """Load user-defined allowed patterns from config file."""
    config_path = os.path.expanduser("~/.claude/hooks/safety_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            return [p for p in config.get("allow_patterns", [])]
        except (json.JSONDecodeError, IOError):
            pass
    return []


def log_blocked(command, reason):
    """Log a blocked command attempt."""
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().isoformat()
    project = os.getcwd()
    entry = json.dumps({
        "timestamp": timestamp,
        "command": command,
        "project_path": project,
        "reason": reason
    })
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def check_command(command):
    """Check if a command should be blocked. Returns (blocked, reason)."""
    # Check allowed patterns first
    extra_allowed = load_allow_config()
    all_allowed = ALLOWED_PATTERNS + extra_allowed
    for pattern in all_allowed:
        if re.search(pattern, command, re.IGNORECASE):
            return False, None

    # Check blocked patterns
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason

    return False, None


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason)
        msg = f"BLOCKED: Dangerous command detected ({reason}). " \
              f"Command: '{command[:80]}...' " \
              f"This attempt has been logged to {LOG_FILE}"
        result = {
            "decision": "block",
            "reason": msg
        }
        print(json.dumps(result))
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
