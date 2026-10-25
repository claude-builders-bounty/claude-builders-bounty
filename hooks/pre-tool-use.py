#!/usr/bin/env python3
"""
Pre-Tool-Use Security Hook for Claude Code
Repository: claude-builders-bounty
Author: @satyadilip
Target Issue: #3 ($100 USD)

Intercepts and blocks destructive bash commands before execution in Claude Code:
- Recursive forced wipes (rm -rf)
- Forced Git rewrites (git push --force)
- Destructive SQL statements (DROP TABLE, TRUNCATE, DELETE FROM without WHERE)
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

# Target patterns & explicit human-readable violation descriptions
BLOCKED_PATTERNS = [
    (
        r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+-[a-zA-Z]*[rf][a-zA-Z]*|-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)\b",
        "Destructive filesystem wipe (rm -rf / recursive force removal)",
    ),
    (
        r"\bgit\s+push\b.*?(?:--force|-f\b|\+refs/heads/)",
        "Destructive Git remote rewrite (git push --force / forced branch update)",
    ),
    (
        r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b",
        "Destructive database schema deletion (DROP TABLE/DATABASE)",
    ),
    (
        r"\bTRUNCATE(?:\s+TABLE)?\b",
        "Destructive database table wipe (TRUNCATE)",
    ),
    (
        r"\bDELETE\s+FROM\s+[`\"'\w.]+(?:\s*(?:;|$|\s+))(?!(?:.*?\bWHERE\b))",
        "Unconstrained table deletion (DELETE FROM without WHERE clause)",
    ),
]

LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


def log_violation(command: str, reason: str, cwd: str):
    """Log blocked attempt to ~/.claude/hooks/blocked.log with required schema."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = (
            f"[{timestamp}] BLOCKED: {reason}\n"
            f"  Command: {command.strip()}\n"
            f"  Project Path: {cwd}\n"
            f"{'-' * 60}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to {LOG_FILE}: {e}\n")


def is_blocked(command: str):
    """Check command against blocked regex list. Returns (blocked: bool, reason: str)."""
    clean_cmd = command.strip()
    for pattern, reason in BLOCKED_PATTERNS:
        # Check case-insensitively for SQL/bash keywords
        if re.search(pattern, clean_cmd, re.IGNORECASE | re.DOTALL):
            # Special check for DELETE FROM: ensure WHERE isn't in a subsequent line or part
            if "DELETE FROM" in reason.upper():
                if re.search(r"\bWHERE\b", clean_cmd, re.IGNORECASE):
                    continue
            return True, reason
    return False, ""


def inspect_command(command: str, cwd: str):
    """Validate command. If destructive, log and exit with error code 1."""
    blocked, reason = is_blocked(command)
    if blocked:
        log_violation(command, reason, cwd)
        error_msg = (
            f"\n🛡️ [CLAUDE CODE SECURITY GUARD] Command Blocked!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ Violation: {reason}\n"
            f"⚠️ Attempted: {command.strip()}\n"
            f"📂 Location:  {cwd}\n"
            f"📜 Audit Log: {LOG_FILE}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Action Required: Modify command to avoid destructive operations.\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)


def extract_command(raw_input: str) -> str:
    """Extract command from JSON tool payload or raw text."""
    raw = raw_input.strip()
    if not raw:
        return ""
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            # Standard Claude Code Hook input shapes
            if "command" in data:
                return data["command"]
            if "tool_input" in data and isinstance(data["tool_input"], dict):
                return data["tool_input"].get("command", "")
            if "input" in data and isinstance(data["input"], dict):
                return data["input"].get("command", "")
        except json.JSONDecodeError:
            pass
    return raw


def main():
    cwd = os.getcwd()

    # 1. Check CLI arguments
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        inspect_command(cmd, cwd)
        sys.exit(0)

    # 2. Check STDIN (Claude Code Pre-Tool-Use pipeline)
    if not sys.stdin.isatty():
        try:
            raw_data = sys.stdin.read()
            cmd = extract_command(raw_data)
            if cmd:
                inspect_command(cmd, cwd)
        except Exception as e:
            sys.stderr.write(f"Hook processing error: {e}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
