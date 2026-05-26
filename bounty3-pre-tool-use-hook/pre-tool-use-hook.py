#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook

Intercepts dangerous bash commands before execution.
Blocks destructive patterns: rm -rf, DROP TABLE, git push --force,
TRUNCATE, DELETE FROM without WHERE, dd device overwrites, mkfs.

Logs every blocked attempt to ~/.claude/hooks/blocked.log
Returns a clear error message to Claude explaining why the command was blocked.

Usage: Called by Claude Code as a pre-tool-use hook via settings.json:
  {
    "hooks": {
      "PreToolUse": [{
        "matcher": "bash",
        "hooks": [{ "command": "python3 /path/to/pre-tool-use-hook.py" }]
      }]
    }
  }
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Dangerous patterns to block ──────────────────────────────────────
BLOCKED_PATTERNS = [
    # Destructive file operations
    (re.compile(r'\brm\s+-[aRf]*r[aRf]*\b'), "Recursive delete (rm -rf) — use selective removal"),
    (re.compile(r'\brm\s+-rf\b'), "Force recursive delete (rm -rf) — use selective removal"),

    # Git force push
    (re.compile(r'git\s+push\s+--force'), "Git force push — rebase first or create a new branch"),
    (re.compile(r'git\s+push\s+-f\b'), "Git force push (-f) — rebase first or create a new branch"),

    # SQL destructive operations
    (re.compile(r'DROP\s+TABLE', re.IGNORECASE), "DROP TABLE — data loss risk, require explicit confirmation"),
    (re.compile(r'TRUNCATE\s+TABLE', re.IGNORECASE), "TRUNCATE TABLE — data loss risk, use DELETE with WHERE"),
    (re.compile(r'DELETE\s+FROM\s+\w+\s*;?\s*$', re.IGNORECASE), "DELETE without WHERE clause — add WHERE condition"),
    (re.compile(r'DELETE\s+FROM\s+\w+(?!\s+WHERE)', re.IGNORECASE), "DELETE without WHERE clause — add WHERE condition"),

    # Device-level destruction
    (re.compile(r'\bdd\s+.*\bof=/dev/'), "dd device overwrite — irreversible disk destruction"),
    (re.compile(r'\bmkfs\b'), "mkfs filesystem creation — destroys all data on target device"),
    (re.compile(r'>\s*/dev/sd'), "Direct write to block device — data corruption risk"),

    # Other dangerous operations
    (re.compile(r':()\s*{\s*:\s*|&>/dev/null\s*sd'), "Shell fork bomb / dev nuller — resource exhaustion"),
    (re.compile(r'chmod\s+-R\s+777'), "chmod -R 777 — removes all security permissions"),
    (re.compile(r'shutdown\s+(now|-\w*h\s*\d)'), "System shutdown command — requires manual confirmation"),
    (re.compile(r'reboot\b'), "System reboot — requires manual confirmation"),
]

# Commands that are always allowed (false positive safe-list)
ALLOWED_CONTEXTS = [
    # Comments / strings that contain these patterns harmlessly
    (re.compile(r'#.*rm\s+-rf'), "comment"),
    (re.compile(r'echo\s+["\'].*rm\s+-rf'), "echo string"),
    (re.compile(r'"[^"]*rm\s+-rf[^"]*"'), "quoted string"),
    (re.compile(r"'[^']*rm\s+-rf[^']*'"), "single-quoted string"),
    (re.compile(r'//.*DROP\s+TABLE'), "code comment"),
]


def get_log_path():
    """Return path to blocked log file."""
    return os.path.expanduser("~/.claude/hooks/blocked.log")


def ensure_log_dir():
    """Ensure log directory exists."""
    log_path = get_log_path()
    log_dir = os.path.dirname(log_path)
    os.makedirs(log_dir, exist_ok=True)


def log_blocked(command: str, reason: str, cwd: str):
    """Append blocked attempt details to log file."""
    ensure_log_dir()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Command : {command}\n"
        f"  Reason  : {reason}\n"
        f"  Path    : {cwd}\n"
        f"{'─' * 60}\n"
    )
    with open(get_log_path(), "a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if command contains any blocked patterns.
    Returns (is_blocked, reason).
    """
    # Check safe-list first (allow comments, echo statements, quoted strings)
    for pattern, ctx in ALLOWED_CONTEXTS:
        if pattern.search(command):
            return False, ""

    # Check against blocked patterns
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, reason

    return False, ""


def main():
    """Main entry point — reads stdin JSON from Claude Code hook protocol."""
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            # No input = allow (pass-through mode for testing)
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)

        data = json.loads(raw_input)
        command = ""
        cwd = os.getcwd()

        # Claude Code hook protocol: tool_input contains the bash command
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        if isinstance(tool_input, dict):
            command = tool_input.get("command", "")
            cwd = tool_input.get("cwd", cwd)
        elif isinstance(tool_input, str):
            command = tool_input

        if not command:
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)

        is_blocked, reason = check_command(command)

        if is_blocked:
            log_blocked(command, reason, cwd)

            error_msg = (
                f"🛑 COMMAND BLOCKED by pre-tool-use safety hook\n\n"
                f"**Reason:** {reason}\n\n"
                f"**Blocked command:** `{command[:200]}`\n\n"
                f"If this is intentional (e.g., in a test/Docker container), "
                f"temporarily disable the hook in `.claude/settings.json`.\n\n"
                f"This attempt has been logged to `~/.claude/hooks/blocked.log`."
            )
            result = {
                "decision": "block",
                "error_message": error_msg,
            }
            print(json.dumps(result))
            sys.exit(1)
        else:
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)

    except json.JSONDecodeError:
        # If we can't parse input, allow (fail-open for non-hook contexts)
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    except Exception as e:
        # Unexpected error — log but allow (fail-safe)
        ensure_log_dir()
        timestamp = datetime.now(timezone.utc).isoformat()
        with open(get_log_path(), "a") as f:
            f.write(f"[{timestamp}] HOOK_ERROR: {e}\n")
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)


if __name__ == "__main__":
    main()
