#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker

Reads a JSON payload from stdin, checks for dangerous bash commands,
and outputs a JSON response to stdout indicating allow or block.

Install: place in ~/.claude/hooks/ and register in ~/.claude/settings.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


# ─── Dangerous patterns ───────────────────────────────────────────────────────

BLOCKED_PATTERNS = [
    # Shell: recursive forced removal
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--force\s+--recursive|--recursive\s+--force)\b",
     "rm -rf: recursive forced file deletion"),
    (r"\brm\s+-rf\b", "rm -rf: recursive forced file deletion"),
    (r"\brm\s+-fr\b", "rm -rf: recursive forced file deletion"),

    # Git: force push (various forms)
    (r"\bgit\s+push\s+.*--force\b", "git push --force: overwrites remote history"),
    (r"\bgit\s+push\s+.*-f\b",      "git push -f: overwrites remote history"),
    (r"\bgit\s+push\s+--force\b",   "git push --force: overwrites remote history"),

    # SQL: DROP TABLE
    (r"\bDROP\s+TABLE\b", "DROP TABLE: permanently destroys a database table"),

    # SQL: TRUNCATE (removes all rows without WHERE)
    (r"\bTRUNCATE\b", "TRUNCATE: removes all rows from a table"),

    # SQL: DELETE FROM without WHERE clause
    # Matches DELETE FROM <table> not followed by WHERE (case-insensitive)
    (r"\bDELETE\s+FROM\s+\S+\s*(?!WHERE\b)(?:;|$)", "DELETE FROM without WHERE: deletes all rows"),
]

# Compile once, case-insensitive for SQL keywords
_COMPILED = [
    (re.compile(pat, re.IGNORECASE | re.MULTILINE), reason)
    for pat, reason in BLOCKED_PATTERNS
]

# ─── Logging ──────────────────────────────────────────────────────────────────

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def _ensure_log_dir() -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def _log_blocked(command: str, cwd: str, reason: str) -> None:
    _ensure_log_dir()
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] BLOCKED | reason={reason!r} | cwd={cwd!r} | command={command!r}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError:
        # Best-effort logging; never crash the hook
        pass


# ─── Core logic ───────────────────────────────────────────────────────────────

def check_command(command: str) -> tuple[bool, str]:
    """
    Returns (should_block, reason).
    Runs each compiled pattern against the command string.
    """
    for pattern, reason in _COMPILED:
        if pattern.search(command):
            return True, reason
    return False, ""


def process(payload: dict) -> dict:
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Only inspect Bash tool calls
    if tool_name != "Bash":
        return {"action": "allow"}

    command = tool_input.get("command", "")
    if not command:
        return {"action": "allow"}

    should_block, reason = check_command(command)

    if not should_block:
        return {"action": "allow"}

    # Determine project path for the log (use cwd of this process as proxy)
    cwd = os.getcwd()

    _log_blocked(command, cwd, reason)

    message = (
        f"BLOCKED by pre-tool-use safety hook.\n"
        f"Reason: {reason}\n\n"
        f"The following command was NOT executed:\n"
        f"  {command}\n\n"
        f"This command matches a destructive pattern and has been blocked to "
        f"prevent accidental data loss. If you genuinely need to run this "
        f"command, ask the user to run it manually in a terminal.\n\n"
        f"Blocked attempt logged to: {LOG_FILE}"
    )

    return {"action": "block", "message": message}


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        # Malformed input: allow through and don't crash
        result = {"action": "allow"}
        sys.stdout.write(json.dumps(result))
        sys.stdout.flush()
        return

    result = process(payload)
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
