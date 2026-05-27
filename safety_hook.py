#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
Blocks destructive bash commands before execution.

Install:
  mkdir -p ~/.claude/hooks && cp safety_hook.py ~/.claude/hooks/

  Then add to ~/.claude/settings.json (merge with existing content):
  {
    "hooks": {
      "PreToolUse": [
        {
          "command": "python3 ~/.claude/hooks/safety_hook.py",
          "matcher": "Bash",
          "type": "command"
        }
      ]
    }
  }

  WARNING: Do NOT overwrite your existing settings.json! Merge the hooks
  section into your existing configuration. If you have no settings.json
  yet, you can create it with the JSON above.
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

# Maximum log file size in bytes (default 1 MB). Set to 0 to disable rotation.
LOG_MAX_SIZE = int(os.environ.get("SAFETY_HOOK_LOG_MAX_SIZE", 1_048_576))

# Module-level cache for allowed patterns
_allow_config_cache = None
_allow_config_mtime = None


def load_allow_config():
    """Load user-defined allowed patterns from config file (cached)."""
    global _allow_config_cache, _allow_config_mtime

    config_path = os.path.expanduser("~/.claude/hooks/safety_config.json")

    # Check if we can use the cache
    try:
        current_mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else None
    except OSError:
        current_mtime = None

    if _allow_config_cache is not None and current_mtime == _allow_config_mtime:
        return _allow_config_cache

    # Load fresh config
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            _allow_config_cache = [p for p in config.get("allow_patterns", [])]
        except (json.JSONDecodeError, IOError):
            _allow_config_cache = []
    else:
        _allow_config_cache = []

    _allow_config_mtime = current_mtime
    return _allow_config_cache


def _rotate_log_if_needed():
    """Rotate the log file if it exceeds LOG_MAX_SIZE."""
    if LOG_MAX_SIZE <= 0:
        return
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > LOG_MAX_SIZE:
            backup = LOG_FILE + ".1"
            if os.path.exists(backup):
                os.unlink(backup)
            os.rename(LOG_FILE, backup)
    except OSError:
        pass


def log_blocked(command, reason):
    """Log a blocked command attempt."""
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    _rotate_log_if_needed()
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
        # Only append ellipsis when truncation actually occurs
        display_cmd = command if len(command) <= 80 else command[:80] + "..."
        msg = f"BLOCKED: Dangerous command detected ({reason}). " \
              f"Command: '{display_cmd}' " \
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
