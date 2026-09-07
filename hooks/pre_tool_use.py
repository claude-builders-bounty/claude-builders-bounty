#!/usr/bin/env python3
"""
Pre-Tool-Use Destructive Command Blocker Hook for Claude Code / Agents.

Blocks dangerous commands:
- rm -rf
- DROP TABLE
- git push --force / git push -f
- TRUNCATE
- DELETE FROM without a WHERE clause

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import sys
import os
import re
import json
from datetime import datetime

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

FORBIDDEN_PATTERNS = [
    (r"\brm\s+-[rRfF]*[rR][rRfF]*\s+", "Destructive recursive file deletion (rm -rf)"),
    (r"\bDROP\s+TABLE\b", "Destructive SQL table drop (DROP TABLE)"),
    (r"\bTRUNCATE\b", "Destructive SQL table truncation (TRUNCATE)"),
    (r"\bgit\s+push\s+.*(--force|-f)\b", "Destructive forced git history overwrite (git push --force)"),
]

def log_blocked(command: str, reason: str, cwd: str):
    os.makedirs(os.path.dirname(BLOCKED_LOG_PATH), exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason} | CWD: {cwd} | CMD: {command}\n"
    try:
        with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def evaluate_command(command: str, cwd: str = ".") -> tuple[bool, str]:
    # Check regex patterns
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason, cwd)
            return False, reason

    # Check DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE) and not re.search(r"\bWHERE\b", command, re.IGNORECASE):
        reason = "Unbounded SQL table deletion (DELETE FROM without WHERE clause)"
        log_blocked(command, reason, cwd)
        return False, reason

    return True, ""

def main():
    # Read payload from stdin (Claude Code hook format)
    try:
        raw_input = sys.stdin.read().strip()
        data = json.loads(raw_input) if raw_input else {}
    except Exception:
        data = {}

    command = data.get("command") or data.get("args", {}).get("command") or " ".join(sys.argv[1:])
    cwd = data.get("cwd") or os.getcwd()

    if not command:
        sys.exit(0)

    allowed, reason = evaluate_command(command, cwd)
    if not allowed:
        print(f"🛑 SECURITY HOOK INTERCEPTED: Command blocked due to security policy.", file=sys.stderr)
        print(f"Reason: {reason}", file=sys.stderr)
        print(f"Attempted Command: {command}", file=sys.stderr)
        print(f"Logged to: {BLOCKED_LOG_PATH}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
