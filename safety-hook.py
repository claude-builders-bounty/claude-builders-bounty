#!/usr/bin/env python3
"""
Claude Code Safety Pre-Tool-Use Hook
=====================================
Blocks dangerous bash commands before execution.
Logs all blocked attempts with timestamp, command, and project path.

Install: cp safety-hook.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/safety-hook.py
"""

import json
import re
import os
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# ── Dangerous patterns ──────────────────────────────────────────────────────
# Each entry: (regex, reason)
DANGEROUS_PATTERNS = [
    # File system destruction
    (r'\brm\s+(-rf?|--recursive)\s*/', 'Recursive root deletion (rm -rf /)'),
    (r'\brm\s+(-rf?|--recursive)\s+\S*\s*$', 'Recursive force delete (rm -rf)'),
    # Database destruction
    (r'\bDROP\s+TABLE', 'DROP TABLE — irreversible data loss'),
    (r'\bTRUNCATE\b', 'TRUNCATE — bulk data deletion'),
    (r'\bDELETE\s+FROM\b(?!\s*\S*\s+WHERE\s)', 'DELETE FROM without WHERE clause'),
    # Git destructive
    (r'\bgit\s+push\s+--force\b', 'git push --force — branch overwrite'),
    (r'\bgit\b.*\breset\b.*\b--hard\b', 'git reset --hard — history rewrite'),
    # System destruction
    (r'\b(mkfs|fdisk|dd|format)\s', 'Disk formatting operation'),
    (r'\bchmod\s+777\s+/', 'World-writable root permissions'),
]

# ── Safe patterns (explicitly allow) ─────────────────────────────────────────
SAFE_PATTERNS = [
    r'\brm\s+(-rf?|--recursive)\s+\.\/?\s*$',  # rm -rf ./
    r'\brm\s+(-rf?|--recursive)\s+\S+target',    # rm -rf build/target
]


def check_dangerous(command: str) -> tuple[bool, str]:
    """Check if a command is dangerous. Returns (is_blocked, reason)."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check if it matches a safe pattern
            for safe in SAFE_PATTERNS:
                if re.match(safe, command, re.IGNORECASE):
                    return False, ""
            return True, reason
    return False, ""


def log_blocked(command: str, reason: str, cwd: str):
    """Log a blocked command attempt with timestamp."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "command": command,
                "reason": reason,
                "project_path": cwd,
            }
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # Failing to log should not crash the hook


def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Not a valid event — allow
        return

    # Only intercept Bash tool calls
    if event.get("event_name") != "PreToolUse":
        return

    tool_name = event.get("tool_name", "")

    if tool_name not in ("Bash", "bash"):
        return  # Only block bash commands

    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)

    if not command.strip():
        return

    is_blocked, reason = check_dangerous(command)

    if is_blocked:
        cwd = event.get("cwd", os.getcwd())
        log_blocked(command, reason, cwd)

        decision = {
            "skip": True,
            "message": (
                f"❌ SAFETY BLOCK: {reason}\n\n"
                f"Command blocked: `{command[:200]}`\n"
                f"To proceed, use an explicit safe alternative or"
                f" run it manually outside Claude Code."
            )
        }
        print(json.dumps(decision))
        sys.exit(0)

    # Allow — no output needed
    # Exit code 0 means "no decision" = allow by default
    sys.exit(0)


if __name__ == "__main__":
    main()
