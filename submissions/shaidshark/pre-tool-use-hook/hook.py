#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE.
Override: ALLOW_DESTRUCTIVE=1
"""

import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    # rm -rf: catch -rf, -fr, -r -f, --recursive, --force, and all combinations
    (
        r"\brm\s+.*?(?:-[rRfF]+\b|--recursive\b|--force\b)",
        "CRITICAL",
        "rm -rf detected",
    ),
    # git push --force: catch --force, -f, --force-with-lease
    (
        r"\bgit\s+push\s+.*?(?:--force\b|-f\b)",
        "HIGH",
        "git push --force detected",
    ),
    # DROP TABLE
    (r"\bDROP\s+TABLE\b", "CRITICAL", "DROP TABLE detected"),
    # TRUNCATE
    (r"\bTRUNCATE\s+\w+", "HIGH", "TRUNCATE detected"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
MAX_INPUT_LENGTH = 10000


def log_blocked(command, risk, reason):
    """Log blocked command with sanitization to prevent log injection."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Sanitize: strip newlines and control characters to prevent log injection
    safe_command = re.sub(r"[\n\r\x00-\x1f]", " ", command)[:500]
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] BLOCKED (risk={risk}): {reason} | command: {safe_command}\n")
    except OSError as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)


def _check_delete_without_where(command):
    """Check if any DELETE FROM statement lacks a WHERE clause."""
    statements = command.split(";")
    for stmt in statements:
        if re.search(r"\bDELETE\s+FROM\b", stmt, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
                return True
    return False


def main():
    if os.environ.get("ALLOW_DESTRUCTIVE") == "1":
        return 0

    # Read command from stdin (Claude Code hooks receive tool input via stdin)
    command = ""
    try:
        command = sys.stdin.read().strip()
    except Exception:
        pass

    # Also check TOOL_INPUT env var (alternative hook interface)
    if not command:
        command = os.environ.get("TOOL_INPUT", "")

    if not command:
        return 0

    # Input length validation to prevent DoS
    if len(command) > MAX_INPUT_LENGTH:
        log_blocked(command[:100] + "... (truncated)", "HIGH", "Input exceeds maximum length")
        print("BLOCKED: Input too long", file=sys.stderr)
        return 1

    # Check regex patterns
    for pattern, risk, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.DOTALL):
            log_blocked(command, risk, reason)
            print(f"BLOCKED: {reason}", file=sys.stderr)
            print(f"   Risk level: {risk}", file=sys.stderr)
            print(f"   Set ALLOW_DESTRUCTIVE=1 to override.", file=sys.stderr)
            return 1

    # Special check for DELETE FROM without WHERE (statement-aware)
    if _check_delete_without_where(command):
        log_blocked(command, "CRITICAL", "DELETE FROM without WHERE detected")
        print("BLOCKED: DELETE FROM without WHERE detected", file=sys.stderr)
        print("   Risk level: CRITICAL", file=sys.stderr)
        print("   Set ALLOW_DESTRUCTIVE=1 to override.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
