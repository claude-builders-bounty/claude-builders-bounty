#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
Blocks destructive bash commands before execution.

Install:
  cp safety_hook.py ~/.claude/hooks/safety_hook.py
  Then add the hook config to ~/.claude/settings.json under hooks.PreToolUse
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

DEFAULT_ALLOWED = [
    r'^/tmp/',
    r'^/var/tmp/',
    r'^/node_modules/',
    r'^/test',
    r'^/\.test',
    r'^/__pycache__/',
    r'^/build/',
    r'^/dist/',
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB rotation threshold

# Module-level cache for allow config
_allow_cache = None
_allow_cache_mtime = None


def load_allow_config():
    """Load allowlist from config file, with caching."""
    global _allow_cache, _allow_cache_mtime
    config_path = os.path.expanduser("~/.claude/hooks/allow.json")

    if not os.path.exists(config_path):
        return DEFAULT_ALLOWED

    # Check cache: use mtime to invalidate
    try:
        mtime = os.path.getmtime(config_path)
    except OSError:
        return _allow_cache or DEFAULT_ALLOWED

    if _allow_cache is not None and _allow_cache_mtime == mtime:
        return _allow_cache

    try:
        with open(config_path) as f:
            extra = json.load(f)
        _allow_cache = DEFAULT_ALLOWED + extra.get("allowed_paths", [])
        _allow_cache_mtime = mtime
    except (json.JSONDecodeError, KeyError):
        return _allow_cache or DEFAULT_ALLOWED

    return _allow_cache


def rotate_log_if_needed():
    """Simple size-based log rotation to prevent unbounded growth."""
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
            backup = LOG_FILE + ".1"
            if os.path.exists(backup):
                os.remove(backup)
            os.rename(LOG_FILE, backup)
    except OSError:
        pass


def check_command(command):
    """Check if a command should be blocked. Returns (blocked: bool, reason: str)."""
    allowed_patterns = load_allow_config()

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check if the destructive target is in the allowlist
            for allow_pattern in allowed_patterns:
                if re.search(allow_pattern, command):
                    return False, ""
            return True, reason

    return False, ""


def log_blocked(command, reason):
    """Log a blocked command attempt."""
    rotate_log_if_needed()
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trunc_cmd = command[:80] + ("..." if len(command) > 80 else "")
    entry = json.dumps({"ts": timestamp, "reason": reason, "cmd": trunc_cmd})
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
        tool_input = payload.get("tool_input", {})
        command = tool_input.get("command", "")
    except (json.JSONDecodeError, KeyError):
        sys.exit(0)

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, reason)
        print(f"BLOCKED: {reason}")
        print(f"Command: {command[:80]}{'...' if len(command) > 80 else ''}")
        sys.exit(2)


if __name__ == "__main__":
    main()
