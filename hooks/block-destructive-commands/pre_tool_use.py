#!/usr/bin/env python3
"""
Pre-Tool-Use Security Hook for Claude Code.

Intercepts dangerous bash commands and SQL statements before execution.
Reads the Claude Code hook JSON payload from stdin, inspects the Bash tool
command, and blocks it (exit code 2) when a destructive pattern is matched.

Blocked commands are logged to ~/.claude/hooks/blocked.log with timestamp,
attempted command, project path, and the rule that triggered the block.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HOOK_DIR = Path(os.path.expanduser("~/.claude/hooks"))
LOG_FILE = HOOK_DIR / "blocked.log"

DANGEROUS_PATTERNS = [
    (
        re.compile(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", re.IGNORECASE),
        "rm -rf: recursive force deletion",
    ),
    (
        re.compile(r"\brm\s+--recursive\b.*--force\b|\brm\s+--force\b.*--recursive\b", re.IGNORECASE),
        "rm --recursive --force: recursive force deletion",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE: destructive SQL operation",
    ),
    (
        re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
        "DROP DATABASE: destructive SQL operation",
    ),
    (
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
        "TRUNCATE: table wipeout without row-level control",
    ),
    (
        re.compile(r"\bgit\s+push\s+.*(?:--force(?:-with-lease)?|-f\b)", re.IGNORECASE),
        "git push --force: overwrites remote history",
    ),
    (
        re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.IGNORECASE),
        "DELETE FROM without WHERE: unbounded deletion",
    ),
]


def log_blocked(command: str, reason: str, cwd: str) -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] BLOCKED | cmd: {command} | reason: {reason} | path: {cwd}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def check_command(command: str) -> str | None:
    """Return a reason string if the command should be blocked, else None."""
    if not command:
        return None
    clean = command.strip()
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(clean):
            return reason
    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    cwd = payload.get("cwd") or os.getcwd()

    reason = check_command(command)
    if reason:
        log_blocked(command, reason, cwd)
        sys.stderr.write(
            f"\nBlocked: {reason}\n"
            f"Command: {command}\n"
            f"This command was intercepted by the pre-tool-use security hook.\n"
            f"Logged to {LOG_FILE}\n"
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
